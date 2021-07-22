#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @File  : views.py
# @Author: kaixin.xu
# @Date  : 2020/9/11
# @Desc  : 接口内函数相关接口
from utils.function_files import parse_function, extract_functions

from flask import Blueprint, request, current_app
from flask_restful import Api

func = Blueprint('func', __name__, url_prefix='/func')
from utils import restful

api = Api(func)
import os, config, types, importlib, traceback


@func.route('/find', methods=['POST'])
def get_func():
    """ 获取函数文件信息 """
    data = request.json
    func_name = data.get('funcName')
    if not func_name:
        return restful.params_error(message="请输入文件名")
    if not os.path.exists('{}/{}'.format(config.FUNC_ADDRESS, func_name)):
        return restful.params_error(message="文件名不存在")
    with open('{}/{}'.format(config.FUNC_ADDRESS, func_name), 'r', encoding='utf8') as f:
        d = f.read()
    return restful.success(data=d)


@func.route('/getPythonFiles')
def get_funcs():
    """ 查找所以Python函数文件 """
    files = []
    for root, dirs, files in os.walk(os.path.abspath('.') + r'/func_list'):
        if '__init__.py' in files:
            files.remove('__init__.py')
        files = [{'value': f} for f in files]
        break
    return restful.success(data=files)


@func.route('/save', methods=['POST'])
def save_func():
    """ 保存函数文件 """
    data = request.json
    func_data = data.get('funcData')
    func_name = data.get('funcName')
    if not os.path.exists('{}/{}'.format(config.FUNC_ADDRESS, func_name)):
        return restful.params_error(message="文件名不存在")

    with open('{}/{}'.format(config.FUNC_ADDRESS, func_name), 'w', encoding='utf8') as f:
        f.write(func_data)
    return restful.success(message="保存成功")


def is_function(tup):
    """ Takes (name, object) tuple, returns True if it is a function.
    """
    name, item = tup
    return isinstance(item, types.FunctionType)


@func.route('/check', methods=['POST'])
def check_func():
    """ 函数调试 """
    data = request.json
    func_file_name = data.get('funcFileName')
    func_name = data.get('funcName')
    if not os.path.exists('{}/{}'.format(config.FUNC_ADDRESS, func_file_name)):
        return restful.params_error(message="文件名不存在")
    try:
        import_path = 'func_list.{}'.format(func_file_name.replace('.py', ''))
        func_list = importlib.reload(importlib.import_module(import_path))
        module_functions_dict = {name: item for name, item in vars(func_list).items() if
                                 isinstance(item, types.FunctionType)}

        ext_func = extract_functions(func_name)
        if len(ext_func) == 0:
            return restful.params_error(message="函数解析失败，注意格式问题")
        func = parse_function(ext_func[0])
        relust = module_functions_dict[func['func_name']](*func['args'])
        print(relust)
        print(type(relust))
        return restful.success(message="请查看", data=relust)

    except Exception as e:
        current_app.logger.info(str(e))
        error_data = '\n'.join('{}'.format(traceback.format_exc()).split('↵'))
        return restful.params_error(message="语法错误，请自行检查", data=error_data)


@func.route('/create', methods=['POST'])
def create_func():
    """ 创建函数文件 """
    data = request.json
    func_name = data.get('funcName')
    if func_name.find('.py') == -1:
        return restful.params_error(message="请创建正确格式的py文件")
    if not func_name:
        return restful.params_error(message="文件名不能为空")
    if os.path.exists('{}/{}'.format(config.FUNC_ADDRESS, func_name)):
        return restful.params_error(message="文件名已存在")
    with open('{}/{}'.format(config.FUNC_ADDRESS, func_name), 'w', encoding='utf8') as f:
        pass
    return restful.success("创建成功")


@func.route('/remove', methods=['POST'])
def remove_func():
    """ 删除函数文件 """
    data = request.json
    func_name = data.get('funcName')
    if not os.path.exists('{}/{}'.format(config.FUNC_ADDRESS, func_name)):
        return restful.params_error(message="文件名不存在")

    else:
        os.remove('{}/{}'.format(config.FUNC_ADDRESS, func_name))
    return restful.success(message="删除成功")
