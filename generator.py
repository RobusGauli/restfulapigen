__author__ ='robusgauli@gmail.com'


import os
import sys
import re
import json
import functools
import itertools


from flask import jsonify
from flask import request

from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.exc import IntegrityError
from sqlalchemy.exc import DataError

from restfulapigen.envelop import (
    fatal_error_envelop,
    json_records_envelop,
    record_updated_envelop,
    record_created_envelop,
    record_notfound_envelop,
    record_exists_envelop,
    record_deleted_envelop,
    data_error_envelop,
    validation_error_envelop
)

from restfulapigen.errors import (
    PrimaryKeyNotFound
)


format_error = lambda _em : \
                    re.search(r'\n.*\n', _em).group(0).strip().capitalize()

format_data_error = lambda _em : \
                    re.search(r'\).*\n', _em).group(0)[1:].strip().capitalize()

valid_file = lambda v_file : os.path.exists(v_file) \
                    and os.path.isfile(v_file) and os.path.splitext(v_file)[1] == '.json'



def new_method(model_name):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            model_name = func
            return model_name(*args, **kwargs)
        return wrapper
    return decorator





class RESTApi:

    def __init__(self, app, db_session, validation_file = None):
        self.app = app
        self.db_session = db_session
        
        if validation_file is not None and valid_file(validation_file):
            #this is valid json file
            self._validation = json.loads(open(validation_file).read())
        else:
            self._validation = None
        
            
    def get_for(self, model, 
                    before_response_for_resources=None, 
                    before_response_for_resource=None):

        if not model.__mapper__.primary_key:
            raise PrimaryKeyNotFound('Primary key not found in % table' % model.__tablename__)
    
        _primary_key = model.__mapper__.primary_key[0].name
        
        
        def _get_resources():
            results = self.db_session.query(model).all()
            _list_data = list({
                key : val for key, val in vars(r).items()
                if not key.startswith('_')
            } for r in results)

            #if after request if not not then call the predicate
            if before_response_for_resources:
                before_response_for_resources(_list_data)
            
            return jsonify(json_records_envelop(_list_data))
        _get_resources.__name__ = 'get_all' + model.__tablename__ 

        self.app.route('/%s' % model.__tablename__)(_get_resources)

        
        def _get_resource(r_id):
            try:

                result = self.db_session.query(model).\
                            filter(getattr(model, _primary_key) == r_id).one()
            except NoResultFound:
                return record_notfound_envelop()

            _data = {
                key : val for key, val in vars(result).items()
                if not key.startswith('_')
            }

            if before_response_for_resource:
                before_response_for_resource(_data)
            return jsonify(json_records_envelop(_data))
        _get_resource.__name__ = 'get' + model.__tablename__

        self.app.route('/%s/<int:r_id>' % model.__tablename__)(_get_resource)
    

    def update_for(self, model, 
                    before_response_for_resource=None):
        if not model.__mapper__.primary_key:
            raise PrimaryKeyNotFound('Primary key not found in % table' % model.__tablename__)
    
        _primary_key = model.__mapper__.primary_key[0].name
        
        def _update_resource(id):
            try:
                self.db_session.query(model).filter(getattr(model, _primary_key) == id).update(request.json)
                self.db_session.commit()
            except IntegrityError as e:
                return record_exists_envelop(format_error(str(e)))
            except DataError as e:
                return data_error_envelop(format_data_error(str(e)))
            else:
                return record_updated_envelop(request.json)

        _update_resource.__name__ = 'put' + model.__tablename__
        #add the route 
        self.app.route('/%s/<int:id>' % model.__tablename__, methods=['PUT'])(_update_resource)
    

    def post_for(self, model):

        def _post():
            if self._validation and model.__name__ in self._validation:
                valid, err = validate(self._validation[model.__name__], request.json)
                if not valid:
                    return validation_error_envelop(err)
            try:
                self.db_session.add(model(**request.json))
                self.db_session.commit()
            
            except IntegrityError as e:
                return record_exists_envelop(format_error(str(e)))
            except DataError as e:
                return data_error_envelop(format_data_error(str(e)))
            else:
                return record_created_envelop(request.json)
        
        #change the name of the function 
        _post.__name__ = 'post' + model.__tablename__
        self.app.route('/%s' % model.__tablename__, methods=['POST'])(_post)
    
    def delete_for(self, model):

        if not model.__mapper__.primary_key:
            raise PrimaryKeyNotFound('Primary Key Not Found in %s table' % model.__tablename__)
        
        #get the primary_key
        _primary_key = model.__mapper__.primary_key[0].name
        def _delete(id):
            try:
                _resource = self.db_session.query(model).filter(getattr(model, _primary_key) == id).one()
                self.db_session.delete(_resource)
                self.db_session.commit()
            except NoResultFound:
                return record_notfound_envelop()
            else:
                return record_deleted_envelop()
        
        _delete.__name__ = 'delete_' + model.__tablename__

        self.app.route('/%s/<int:id>' % model.__tablename__, methods=['DELETE'])(_delete)
    

    def rest_for(self, model):
        '''Apply all the http methods for the resources'''
        self.get_for(model)
        self.post_for(model)
        self.delete_for(model)
        self.update_for(model)




def validate(validation, data):
    #get all the keys from data that are to be validated
    _keys = list(data.keys() & validation.keys())

    for key in _keys:
        #get the val
        _val = data[key]
        
        if validation[key].get('not_null', None) and _val is None:
            return False, 'Value for key %r cannot be Null/None' %(key)

        if isinstance(_val, int):
            if validation[key].get('max_val', None) and _val >= validation[key]['max_val']:
                return False, 'Integer value for %r cannot be greater than  %s' % (key, validation[key]['max_val'])
            
            if validation[key].get('min_val', None) and _val <= validation[key]['min_val']:
                return False, 'Integer value for %r cannot be less than %s' %(key, validation[key]['min_val'])
    
        if validation[key].get('max_len', None) and not len(str(_val)) <= validation[key]['max_len']:
            return False, 'Value for key %r cannot have length more than %s' % (key, validation[key]['max_len'])
        
        if validation[key].get('min_len', None) and not len(str(_val)) >= validation[key]['min_len']:
            return False, 'Value for key %r cannot have length less than %s' % (key, validation[key]['min_len'])
        
        
    
    return True, None
    
