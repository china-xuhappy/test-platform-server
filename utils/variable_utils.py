"""
动态参数 类
针对用例 生成动态参数 获取动态参数

"""

import copy

# 请求接口动态参数
import datetime
import os, re, config, types, importlib
from flask import current_app
from config import USERID
from utils.function_files import extract_functions, parse_function

requestVariableDict = {

}
# 用户动态参数
userVariableDict = {

}
# 定时任务动态参数
taskVariableDict = {

}


def create_variable(variableName, variableValue, local_id=None, space="requestVariable", typeOptions="", files=None):
    """
    创建动态参数
    :param files:
    :param variableName:  创建名
    :param variableValue: 创建值
    :param local_id: 存储动态参数里面独立空间
    :param typeOptions: 创建类型 str int json interface
    :param space: 创建到那个空间
    :return:
    """

    global requestVariableDict, taskVariableDict, userVariableDict

    current_app.logger.info(
        "utils.variable_utils.create_variable -> parameter "
        "variableName:{variableName} ,variableValue:{variableValue}, local_id:{local_id},space:{space}, "
        "requestVariableDict:{requestVariableDict},taskVariableDict:{taskVariableDict}, userVariableDict:{userVariableDict}".format(
            variableName=variableName, variableValue=variableValue, local_id=local_id, space=space
            , requestVariableDict=requestVariableDict, taskVariableDict=taskVariableDict,
            userVariableDict=userVariableDict))

    variable_dict = requestVariableDict

    if space == "userVariable":
        variable_dict = userVariableDict
    elif space == "taskVariable":
        variable_dict = taskVariableDict

    result = variableValue

    # string int 都不关，直接赋值
    variableLocalDict = {}
    if local_id is not None:
        if local_id not in variable_dict:
            variable_dict[local_id] = {}
        variableLocalDict = copy.deepcopy(variable_dict[local_id])  # 开辟一个局部空间

    if variableName is None and isinstance(result, dict):
        variableLocalDict.update(get_variable(result, local_id, files))
    else:
        if result is not None:
            variableLocalDict[variableName] = get_variable(result, local_id, files)

    if local_id is not None:
        if local_id in variable_dict:
            variable_dict[local_id].update(variableLocalDict)
        else:
            variable_dict[local_id] = variableLocalDict
    else:
        variable_dict.update(variableLocalDict)
    return result


def get_str_dynamic(string, local_id=None, files=None):
    """
    获取动态参数
    :param files: python 文件
    :param string:
    :param local_id:
    :return:
    """
    current_app.logger.info(
        "utils.variable_utils.get_str_dynamic -> parameter dynamicContent:{dynamicContent} , local_id:{local_id}".format(
            dynamicContent=string, local_id=local_id))

    dynamicResult = ""
    dynamicList = re.findall("\\${(.+?)\\}", string)
    for dynamicStr in dynamicList:
        var = "${" + dynamicStr + "}"
        try:
            dynamicResult = get_variable(var, local_id, files)
            string = str(string).replace(var, str(dynamicResult))

            current_app.logger.info(
                "utils.variable_utils.get_str_dynamic -> 获取动态参数 succeed dynamicContent:{dynamicContent} , local_id:{local_id}, dynamicResult:{dynamicResult}".format(
                    dynamicContent=dynamicStr, local_id=local_id, dynamicResult=dynamicResult))

        except Exception as e:
            current_app.logger.error(
                "utils.variable_utils.get_str_dynamic -> 获取动态参数 fail dynamicContent:{dynamicContent} , local_id:{local_id}, dynamicResult:{dynamicResult} ,error:{e}".format(
                    dynamicContent=dynamicStr, local_id=local_id, dynamicResult=dynamicResult, e=repr(e)))
    return string


def get_file_func(func_name, files_list):
    """
    获取python文件里面方法内容
    :param func_name: 方法
    :param files_list: 文件列表
    :return:
    """
    current_app.logger.info(
        "utils.variable_utils.get_file_func -> 获取python文件方法内容 func_name:{func_name} , files_list:{files_list}".format(
            func_name=func_name, files_list=files_list))

    if files_list is None or len(files_list) == 0:
        current_app.logger.error(
            "utils.variable_utils.get_file_func -> 未找到python文件 func_name:{func_name} , files_list:{files_list}".format(
                func_name=func_name, files_list=files_list))

        return "未找到python文件"

    for file_name in files_list:
        if not os.path.exists('{}/{}'.format(config.FUNC_ADDRESS, file_name)):
            current_app.logger.error(
                "utils.variable_utils.get_file_func -> 文件不存在 func_name:{func_name} , files_list:{files_list}".format(
                    func_name=func_name, files_list=files_list))
            return "文件不存在"
        try:
            import_path = 'func_list.{}'.format(file_name.replace('.py', ''))
            func_list = importlib.reload(importlib.import_module(import_path))
            module_functions_dict = {name: item for name, item in vars(func_list).items() if
                                     isinstance(item, types.FunctionType)}

            ext_func = extract_functions(func_name)
            if len(ext_func) == 0:
                current_app.logger.error(
                    "utils.variable_utils.get_file_func -> 函数解析失败，注意格式问题 func_name:{func_name} , files_list:{files_list}".format(
                        func_name=func_name, files_list=files_list))

                return "函数解析失败，注意格式问题"
            func = parse_function(ext_func[0])
            relust = module_functions_dict[func['func_name']](*func['args'])
            return relust
        except Exception as e:
            current_app.logger.error(
                "utils.variable_utils.get_file_func -> 代码系统异常 func_name:{func_name} , files_list:{files_list} , e: {e}".format(
                    func_name=func_name, files_list=files_list, e=repr(e)))
            return "代码系统异常"


def get_variable(params, local_id=None, files=None):
    """
    获取动态参数值
    从已有的动态参数 存放空间 去查找
    :param params: 参数值
    :param local_id: 空间id
    :param files: python 文件
    :return:
    """
    current_app.logger.info(
        "utils.variable_utils.get_variable -> parameter params:{params} , local_id:{local_id}".format(
            params=params, local_id=local_id))

    if isinstance(params, dict):
        for k, v in params.items():
            if isinstance(v, str):
                if str(v).find("${") != -1:
                    variableName = str(v)[2:-1].split(".")  # 把动态参数表示 取出里面的值

                    # 判断是否存在python func，需要执行python方法获取东西
                    if "python" in variableName[0] or "func" in variableName[0]:
                        method = "${" + variableName[0][variableName[0].index("(") + 1: -1] + "}"
                        params[k] = get_file_func(method, files)
                        continue

                    variableValue = cycle_get_variable(variableName, local_id)
                    if variableValue is not None:
                        if variableValue == "true":
                            variableValue = True
                        params[k] = variableValue
                    else:
                        params[k] = v  # 等于原来的

            elif isinstance(v, dict):
                get_variable(params[k], local_id, files)

            elif isinstance(v, list):
                if len(v) >= 1:
                    get_variable(v[0], local_id, files)

    if isinstance(params, list):
        if len(params) >= 1:
            get_variable(params[0], local_id, files)

    if str(params).find("${") != -1:
        variableName = str(params)[2:-1].split(".")

        # 判断是否存在python，需要执行python方法获取东西
        if "python" in variableName[0] or "func" in variableName[0]:
            method = "${" + variableName[0][variableName[0].index("(") + 1: -1] + "}"
            return get_file_func(method, files)
        variableValue = cycle_get_variable(variableName, local_id)
        if variableValue is not None:
            if variableValue == "true":
                variableValue = True
            return variableValue
        else:
            return params  # 等于原来的
    else:
        return params


def cycle_get_variable(parameter, local_id):
    global requestVariableDict, userVariableDict, taskVariableDict

    current_app.logger.info(
        "utils.variable_utils.cycle_get_variable -> parameter parameter:{parameter} , local_id:{local_id}"
        ",requestVariableDict:{requestVariableDict},taskVariableDict:{taskVariableDict}, "
        "userVariableDict:{userVariableDict}".format(
            parameter=parameter, local_id=local_id, requestVariableDict=requestVariableDict,
            taskVariableDict=taskVariableDict, userVariableDict=userVariableDict))

    userLocalDict = {}

    variableValue = ""
    variableDict = []
    if local_id is not None and local_id in requestVariableDict:
        requestLocalDict = copy.deepcopy(requestVariableDict[local_id])
    else:
        requestLocalDict = copy.deepcopy(requestVariableDict)

    if USERID in userVariableDict:
        userLocalDict = copy.deepcopy(userVariableDict[USERID])

    if local_id is not None and local_id in taskVariableDict:
        taskLocalDict = copy.deepcopy(taskVariableDict[local_id])
    else:
        taskLocalDict = copy.deepcopy(taskVariableDict)

    isLook = False
    for i in range(3):  # 循环3次 去查找
        i += 1

        if i == 1:
            variableDict = userLocalDict

        if i == 2:
            variableDict = requestLocalDict

        if i == 3:
            variableDict = taskLocalDict

        num = 0
        for variable in parameter:
            num += 1
            if variableDict is not None and (variable in variableDict or is_number(variable)):
                if is_number(variable):
                    variable = int(variable)
                variableValue = variableDict[variable]
                variableDict = variableDict[variable]
                isLook = True
            else:
                if num == 1:
                    break
    if isLook:
        current_app.logger.info(
            "utils.variable_utils.cycle_get_variable -> 获取成功 parameter:{parameter} , local_id:{local_id}"
            ",variableValue:{variableValue},variableDict:{variableDict}".format(
                parameter=parameter, local_id=local_id, variableValue=variableValue, variableDict=variableDict))
        return variableValue
    else:
        current_app.logger.debug(
            "utils.variable_utils.cycle_get_variable -> 未获取到 parameter:{parameter} , local_id:{local_id}"
            ",variableValue:{variableValue},variableDict:{variableDict}".format(
                parameter=parameter, local_id=local_id, variableValue=None, variableDict=variableDict))
        return None


def is_number(s):
    try:
        int(s)
        return True
    except ValueError:
        pass

    try:
        import unicodedata
        unicodedata.numeric(s)
        return True
    except (TypeError, ValueError):
        pass

    return False


list_backups = []


def list_to_dict(list_content, count):
    """
    list 转 dict
    :param list_content: ["renterGetAndReturnCarDTO", "getKM", "1", "2", "3"]
    :param count: {"renterGetAndReturnCarDTO": {}}
    :return:
    """
    global list_backups
    if isinstance(list_content, list):
        list_backups = list_content
        for index, list1 in enumerate(list_content, 0):
            list_to_dict(list_content[index + 1 if index + 1 != len(list_content) else 0],
                         count[list_content[0 if index == 0 else index + 1]])

    if isinstance(list_content, str):
        if list_content not in count:
            count[list_content] = {}

        del list_backups[0]
        list_to_dict(list_backups, count)

    return count


def find_by_exhaustion(target_key, content, current_dict, result_dict):
    """
    传入内容 和 要变更的json 进行变更内容
    :param target_key: 目标key
    :param content: 要传入的内容
    :param current_dict: 目标json
    :param result_dict: 最终的内容。。。 接口测试用的
    :return:
    """
    for index, key in enumerate(current_dict):
        val = current_dict.get(key)
        if isinstance(val, dict) and key not in result_dict:
            result_dict[key] = {}
        if target_key == key:
            result_dict[key] = content
            # current_dict[key] = content 目标值不变
        elif type(val) == type({}):
            find_by_exhaustion(target_key, content, val, result_dict.get(key))


def find_by_exist(target_key, current_dict):
    """
    判断key是否存在
    :param target_key: 目标key
    :param current_dict: 目标json
    :return:
    """
    for index, key in enumerate(current_dict):
        val = current_dict.get(key)
        if target_key == key:
            return True
        elif type(val) == type({}):
            return find_by_exist(target_key, val)


def params_to_dynamic(params, dynamics):
    if isinstance(params, dict):
        for k, v in params.items():
            if isinstance(v, str) or isinstance(v, int):
                if str(v).find("${") == -1:
                    new_k = "${%s}" % (k)
                    isTrue = False
                    for index, dynamic in enumerate(dynamics, 0):
                        if k == dynamic["variableName"]:
                            isTrue = True
                        if dynamic["variableName"] == "":
                            del dynamics[index]

                    if not isTrue:
                        dynamics.append(
                            {'required': False, 'typeOptions': 'String', 'variableName': k, 'variableValue': [v]})
                    params[k] = new_k
            elif isinstance(v, dict):
                params_to_dynamic(params[k], dynamics)

# dict1 = {
#     "renterGetAndReturnCarDTO1": {
#         "getKM1": "${getKM}",
#         "returnKM": "${returnKM}",
#         "getCarOil": "${getCarOil}",
#         "returnCarOil": "${returnCarOil}"
#     },
#     "renterGetAndReturnCarDTO2": {
#         "getKM2": "${getKM}",
#         "returnKM": "${returnKM}",
#         "getCarOil": "${getCarOil}",
#         "returnCarOil": "${returnCarOil}"
#     },
#     "orderNo": "",
# }
#
# # router = []
# conut_dict = {}
# print(find_by_exhaustion("getKM1", 1111 , dict1, conut_dict))
# print(dict1)
# print(conut_dict)

# print(
#     str(list_to_dict(["renterGetAndReturnCarDTO", "getKM", "1", "2", "3"], {"renterGetAndReturnCarDTO": {}})).replace("'",
