from flask import jsonify

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
