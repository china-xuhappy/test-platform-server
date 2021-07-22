"""
接口返回结果类 restful
"""
from flask import jsonify

class HttpCode(object):
    ok = 200
    unautherror = 203
    paramserror = 400
    servererror = 500


def restful_result(status, message, obj):
    return jsonify({"status": status, "message": message, "obj": obj})


# 成功
def success(message="", data=None):
    return restful_result(status=HttpCode.ok, message=message, obj=data)


# 其他错误
def unauth_error(message):
    return restful_result(HttpCode.unautherror, message=message, obj=None)


# 参数错误
def params_error(message="", data=None):
    return restful_result(HttpCode.paramserror, message=message, obj=data)


# 服务器内部错误
def server_error(message=""):
    return restful_result(HttpCode.servererror, message=message or "服务器内部错误", obj=None)
