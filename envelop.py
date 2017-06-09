from flask import jsonify

def record_created_envelop(data):
    return jsonify({
        'status' : 'OK',
        'code' : 200,
        'message' : 'Resource Successfully created.',
        'data' : data
    })

def json_records_envelop(data):
    return {
        'status' : 'OK',
        'code' : 200,
        'data' : data,
        'message' : 'Success'
    }

def fatal_error_envelop():
    return {
        'status' : 'OK',
        'code' : 404,
        'message' : 'Unknown Error'
    }

def record_updated_envelop(data):
    return jsonify({
        'status': 'OK',
        'code' : 200,
        'message' : 'Resource Successfully updated',
        'data' : data
    })

def record_notfound_envelop():
    return jsonify({
        'status' : 'Fail',
        'code' : 400,
        'message' : 'Resource not found'
    })

def record_exists_envelop(message):
    return jsonify({
        'status' : 'Fail',
        'code' : 404, 
        'message' : message or 'Record already exists!!'
    })
