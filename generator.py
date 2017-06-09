__author__ ='robusgauli@gmail.com'


import os
import sys
import functools
import itertools

from flask import jsonify
from flask import request

from restfulapigen.envelop import (
    fatal_error_envelop,
    json_records_envelop,
    record_updated_envelop
)




class RESTApi:

    def __init__(self, app, db_session):
        self.app = app
        self.db_session = db_session

        #now we are going to keep track of all the models
        
    def get_for(self, model, 
                    before_response_for_resources=None, 
                    before_response_for_resource=None):
        
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
        self.app.route('/home')(_get_resources)
        
        def _get_resource(r_id):
            result = self.db_session.query(model).filter(model.id == r_id).one()
            
            _data = {
                key : val for key, val in vars(result).items()
                if not key.startswith('_')
            }

            if before_response_for_resource:
                before_response_for_resource(_data)
            return jsonify(json_records_envelop(_data))
        self.app.route('/home/<int:r_id>')(_get_resource)
    

    def update_for(self, model, 
                        before_response_for_resource=None):
        
        def _update_resource(id):
            try:
                self.db_session.query(model).filter(model.id == id).update(request.json)
                self.db_session.commit()
                pass
            except Exception:
                return fatal_error_envelop()
            else:
                print(request.json)
                return record_updated_envelop(request.json)
        
        #add the route 
        self.app.route('/home/<int:id>', methods=['PUT'])(_update_resource)
