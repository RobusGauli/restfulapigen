__author__ ='robusgauli@gmail.com'


import os
import sys
import re
import functools
import itertools

from flask import jsonify
from flask import request

from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.exc import IntegrityError

from restfulapigen.envelop import (
    fatal_error_envelop,
    json_records_envelop,
    record_updated_envelop,
    record_created_envelop,
    record_notfound_envelop,
    record_exists_envelop,
    record_deleted_envelop
)

from restfulapigen.errors import (
    PrimaryKeyNotFound
)


format_error = lambda _em : re.search(r'\n.*\n', _em).group(0).strip()

def new_method(model_name):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            model_name = func
            return model_name(*args, **kwargs)
        return wrapper
    return decorator




class RESTApi:

    def __init__(self, app, db_session):
        self.app = app
        self.db_session = db_session

        #now we are going to keep track of all the models
        
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
            else:
                return record_updated_envelop(request.json)

        _update_resource.__name__ = 'put' + model.__tablename__
        #add the route 
        self.app.route('/%s/<int:id>' % model.__tablename__, methods=['PUT'])(_update_resource)
    

    def post_for(self, model):

        def _post():
            try:
                self.db_session.add(model(**request.json))
                self.db_session.commit()
            
            except Exception:
                
                return record_exists_envelop()
            else:
                return jsonify({'message' : 'done'})
        
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
            except Exception:
                raise
            else:
                return record_deleted_envelop()
        
        _delete.__name__ = 'delete_' + model.__tablename__

        self.app.route('/%s/<int:id>' % model.__tablename__, methods=['DELETE'])(_delete)


    
    
    
