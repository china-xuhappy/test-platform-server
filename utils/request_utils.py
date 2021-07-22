#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @File  : request_utils.py
# @Author: kaixin.xu
# @Date  : 2019/12/17
# @Desc  : 接口自动化 请求类，初始化等操作方法
from bson import json_util
from config import USERID
from exts import db, mongo
from controller.project.models import AlterExecuteLog, AlterCaseGather
from utils import restful, assert_utils as assertUtils
from utils.sign_utils import getInterfaceSign1
from utils.variable_utils import get_variable, create_variable, taskVariableDict, find_by_exhaustion, \
    find_by_exist, get_str_dynamic
from flask import current_app
import time,requests,json, copy

requests.packages.urllib3.disable_warnings()
s = requests.session()
s.keep_alive = False
requests.adapters.DEFAULT_RETRIES = 5
from utils.aotu_utils.environment_select_util import get_redis_object,gat_db_object
from controller.project.models import AlterInterface, AlterHost
from controller.project.models import AlterParams, AlterTemplate

gIsFlow = False


def before_init(before, rests):
    """
    前置 参数 初始化 init
    :param before:
    :param rests:
    :return:
    """
    current_app.logger.info(
        "utils.request_utils.before_init -> 入参 before: {before}, rests: {rests}  -->>".format(before=before,
                                                                                              rests=rests))

    # 获取数据
    interfaceName = rests["interfaceName"]
    dynamics = rests["dynamics"]
    paramsInitialTests = rests["paramsInitialTests"]
    interceptor = rests["interceptor"]
    caseId = rests["caseId"]

    # 参数表 里面的断言信息，等前置SQL
    paramsInitialTests = paramsInitialTests[0]
    assertDatas = paramsInitialTests["assertData"]
    beforeSqls = paramsInitialTests["beforeSqls"]
    beforeRedis = paramsInitialTests["beforeRedis"]
    assertSqls = paramsInitialTests["assertSqls"]

    parameters = []
    gatherId = 0
    flowId = 0
    flowName = ""
    flowRests = None
    if "flows" in rests:
        # flow
        flows = rests["flows"]
        parameters = flows["parameters"]
        gatherId = flows["gatherId"]
        flowId = flows["flowId"]
        flowName = flows["flowName"]
        flowRests = flows["flowRests"]
        rests["flowRests"] = flowRests

        flowInitialTests = flows["flowInitialTests"][0]
        flowTests = flowInitialTests["assertData"]
        flowBeforeSqls = flowInitialTests["beforeSqls"]
        flowBeforeRedis = flowInitialTests["beforeRedis"]
        flowAssertSqls = flowInitialTests["assertSqls"]

        for index, assertData in enumerate(assertDatas, 0):
            procedures = assertData[0]["procedures"]
            if procedures[0]["procedure"] == '':
                del assertDatas[index]
        assertDatas = assertDatas + flowTests

        for index, assertSql in enumerate(assertSqls, 0):
            sql = assertSql["sql"]
            if sql == '':
                del assertSqls[index]
        assertSqls = assertSqls + flowAssertSqls

        for index, beforeSql in enumerate(beforeSqls, 0):
            if beforeSql == '':
                del beforeSqls[index]
        beforeSqls = beforeSqls + flowBeforeSqls

        for index, beforeRedisOne in enumerate(beforeRedis, 0):
            if beforeRedisOne == '':
                del beforeRedis[index]
        beforeRedis = beforeRedis + flowBeforeRedis

    rests["assertDatas"] = assertDatas
    rests["assertSqls"] = assertSqls

    # before
    rests["headers"] = before["headers"]
    projectId = before["projectId"]
    paramsId = before["paramsId"]
    params = before["params"]
    paramObj = AlterParams.query.filter(AlterParams.id == paramsId).first()

    if "local_id" in rests:
        local_id = rests["local_id"]
    else:
        rests["local_id"] = None
        local_id = None

    gatherName = ""
    gatherObj = AlterCaseGather.query.filter(AlterCaseGather.id == gatherId).first()
    if gatherObj is not None:
        gatherName = gatherObj.gatherName

    resultObj = {
        "projectId": projectId,
        "paramsId": paramsId,
        "userId": before["userId"],
        "gatherId": gatherId,
        "gatherName": gatherName,
        "flowId": flowId,
        "interfaceName": interfaceName,
        "describe": flowName,
        "flowRests": flowRests,
        "interceptor": interceptor,
        "headers": rests["headers"],  # 请求头
        "dynamicsArgs": dynamics,  # 动态参数
        "caseId": caseId  # 用例Id
    }
    current_app.logger.info(
        "utils.request_utils.before_init -> 插入mongo的resultObj对象: {resultObj} -->>".format(resultObj=resultObj))

    if rests["headers"] is not None:
        rests["headersNew"] = init_headers(rests["headers"])

    rests["paramsNew"] = {}
    files = rests["files"]
    try:
        if dynamics is not None:
            # 添加模板参数
            templateIds = str(paramObj.templateIds).split(",")
            templates = AlterTemplate.query.filter(AlterTemplate.id.in_(templateIds)).all()
            for template in templates:
                params = dict(params, **json.loads(template.templateParams))

            # 添加flow用例 的 参数
            for parameter in parameters:
                key = parameter["variableName"]
                if key.strip() == "":
                    continue

                value = parameter["variableValue"]
                type_option = parameter["typeOptions"]
                value = str(value)
                if type_option == "Int":
                    value = int(value)
                elif type_option == "Json":
                    value = json.loads(value)
                params[key] = value

            paramsNew = init_params(params, dynamics, local_id, files)
            current_app.logger.info(
                "utils.request_utils.before_init -> paramsNew:{paramsNew}".format(paramsNew=paramsNew))

            resultObj["params"] = paramsNew  # 格式化出来的结果
            rests["paramsNew"] = paramsNew

            if projectId == 29 and "sign" in paramsNew:  # interface那个服务需要签名，判断死了， 不然改动有点大
                getInterfaceSign1(paramsNew, paramsNew["sign"])

            # 处理前置SQL 要在处理动态参数后运行。 因为动态参数后面的动态获取是用的动态参数里面的东西，要等初始化
            for beforeIndex in range(len(beforeSqls)):
                beforeSqls[beforeIndex] = get_str_dynamic(beforeSqls[beforeIndex], local_id, files=files)
            init_before_sql(beforeSqls, interceptor)  # 处理前置

            resultObj["beforeSqls"] = beforeSqls

            # 处理前置Reids 要在处理动态参数后运行。 因为动态参数后面的动态获取是用的动态参数里面的东西，要等初始化
            for beforeIndex in range(len(beforeRedis)):
                beforeRedis[beforeIndex] = get_str_dynamic(beforeRedis[beforeIndex], local_id, files=files)
            init_before_redis(beforeRedis,interceptor)  # 处理前置
            resultObj["beforeRedis"] = beforeRedis

    except Exception as e:
        current_app.logger.error("utils.request_utils.before_init -> 前置参数执行失败 error: {e}".format(e=e))
        resultObj["params"] = params
        resultObj["beforeSqls"] = beforeSqls
        resultObj["beforeRedis"] = beforeRedis
        resultObj["useDatas"] = dynamics

    finally:
        rests["resultObj"] = resultObj
        return None


def __request(method, url, isFormData, before, rests=None, isFlow=False):
    run_time = time.perf_counter()
    current_app.logger.info(
        "utils.request_utils.__request -> parameter method: {method}, isFormData: {isFormData},"
        " before: {before}, rests: {rests}, isFlow: {isFlow}, url: {url}"
            .format(method=method, url=url, isFormData=isFormData, before=before, rests=rests, isFlow=isFlow))

    global gIsFlow
    gIsFlow = isFlow
    ovIsError = 0
    caseId = rests["caseId"]
    result = None

    before_init(before, rests)
    headersDict = rests["headersNew"]
    paramsNew = rests["paramsNew"]
    resultObj = rests["resultObj"]
    interceptor = rests["interceptor"]
    local_id = rests["local_id"]
    assertDatas = rests["assertDatas"]
    assert_sqls = rests["assertSqls"]
    dynamics = rests["dynamics"]
    files = rests["files"]
    flowRests = None
    if "flowRests" in rests:
        flowRests = rests["flowRests"]
        if flowRests is not None:
            if "isWaitVariable" in flowRests and flowRests["isWaitVariable"]:
                if "waitValue" in flowRests:
                    waitValue = int(flowRests["waitValue"])
                    time.sleep(waitValue)

    try:

        if method == "POST":
            if str_to_bool(isFormData):
                headersDict["Content-type"] = "application/x-www-form-urlencoded; charset=UTF-8"
                result = requests.post(url, data=paramsNew, headers=headersDict, verify=False)
            else:
                result = requests.post(url, json=paramsNew, headers=headersDict, verify=False)
        elif method == "GET":
            if isinstance(paramsNew, str):
                paramsNew = json.loads(paramsNew)
            result = requests.get(url=url, params=paramsNew, headers=headersDict, verify=False)
        elif method == "PUT":
            if isinstance(paramsNew, str):
                paramsNew = json.loads(paramsNew)
            result = requests.put(url=url, json=paramsNew, headers=headersDict, verify=False)

        if result is not None:
            resultObj["status_code"] = result.status_code
            resultObj["result"] = {}
            if result.status_code != 200:
                current_app.logger.error(
                    "utils.request_utils.__request -> result.status_code != 200 接口请求失败 status_code:{status_code}".format(
                        status_code=result.status_code))
                resultObj["result_text"] = result.text
                return 200, caseId, 1, {}
            try:
                resultJson = result.json()
                if resultJson is None:
                    resultJson = {}
            except Exception as e:
                resultObj["useCase"] = assertDatas
                current_app.logger.error(
                    "utils.request_utils.__request -> result.json() 接口请求失败 result: {result}".format(result=result.text))
                return 500, "接口请求失败: " + str(result.text), 1, {}

            resultObj["useCase"] = assertDatas

            if flowRests is not None:
                if "isVariable" in flowRests and flowRests["isVariable"] and "data" in resultJson:
                    if local_id is not None:
                        space = "taskVariable"
                        create_variable(variableName=flowRests["variableName"], variableValue=resultJson["data"],
                                        local_id=local_id, space=space, files=files)

            if isinstance(resultJson, dict) and "data" in resultJson:
                key = "requestVariable"
                if local_id is not None:
                    key = "taskVariable"
                create_variable(variableName=None, variableValue=resultJson["data"], local_id=local_id, space=key,
                                files=files)

            isError = test(assertDatas, resultJson, local_id, files)  # 调用测试方法
            ovIsError = 0 if isError else 1
            resultObj["result"] = resultJson

            sqls_table_datas = []

            current_app.logger.info(
                "utils.request_utils.__request -> assertSqls :{assertSqls}".format(assertSqls=assert_sqls))

            for assertIndex in range(len(assert_sqls)):
                assert_sqls[assertIndex]["sql"] = get_str_dynamic(assert_sqls[assertIndex]["sql"], local_id,
                                                                  files=files)
                current_app.logger.info(
                    "utils.request_utils.__request -> assertSql :{assertSql}".format(
                        assertSql=assert_sqls[assertIndex]))
                afterData = init_after(assert_sqls[assertIndex], interceptor, local_id=local_id, files=files)  # 处理后置
                if afterData is not None:
                    sqls_table_datas.append(afterData[0])
                    if ovIsError == 0:
                        ovIsError = 0 if afterData[1] else 1

            resultObj["assertSqls"] = sqls_table_datas
            resultObj["status"] = ovIsError

    except Exception as e:
        current_app.logger.error("utils.request_utils.__request -> 方法报错请求失败 error: {e}".format(e=repr(e)))
        return 500, "请求失败(代码内部异常)", 1
    finally:
        ent_time = time.perf_counter()
        waiting = format(ent_time - run_time, '.2f')
        if 1 > float(waiting):
            waiting = float(waiting)
            resultObj["waiting"] = str(waiting * 1000) + "ms"
        else:
            resultObj["waiting"] = waiting + "s"

        # 初始化一下， 预防上面失败返回结果没传参
        if "status" not in resultObj:
            resultObj["status"] = 1

        if "result" not in resultObj:
            resultObj["result"] = {}

        if "assertSqls" not in resultObj:
            resultObj["assertSqls"] = {}

        if "useDatas" not in resultObj:
            resultObj["useDatas"] = dynamics
        current_app.logger.info(
            "utils.request_utils.__request -> resultObj:{resultObj} -->>".format(resultObj=resultObj))

        mongo.db.runLog.insert_one(
            resultObj
        )
        current_app.logger.info("utils.request_utils.__request -> mongo 插入成功 {caseId}: ->".format(caseId=str(caseId)))

    return 200, caseId, ovIsError, resultJson or {}


def str_to_bool(string):
    if isinstance(string, bool):
        return string
    return True if string.lower() == 'true' else False


def init_headers(headers) -> dict:
    headersDict = {}
    for header in headers:
        if header["headersKey"] == '' or header["headersValue"] == '':
            continue
        headersDict[header["headersKey"]] = header["headersValue"]
    return headersDict


def init_params(params, dynamics, local_id=None, files=None):
    """
        初始化参数
        params: 参数
        dynamics: 所有动态参数
        local_id: 存储标识
    """
    local_id_copy = local_id
    paramsCopy = copy.deepcopy(params)
    paramsNew = {}

    if len(dynamics) == 0 or str(paramsCopy).find("${") == -1:
        return paramsCopy
    else:
        # 创建动态参数
        for key, dynamic in dynamics.items():
            for dynamice in dynamic:
                local_id = local_id_copy
                variableName = dynamice["variableName"]
                variableValue = dynamice["variableValue"][0]
                typeOptions = dynamice["typeOptions"]

                if key == "userVariable":
                    local_id = USERID

                if variableName.strip() == "":
                    continue

                if typeOptions == "dict" or typeOptions == "Json":
                    variableValue = json.loads(variableValue)
                    variableValue = get_variable(variableValue, local_id, files)
                if "interfaceDynamic" == key:
                    if "required" in dynamice and dynamice["required"] and not find_by_exist(variableName, paramsNew):
                        find_by_exhaustion(variableName, variableValue, paramsCopy, paramsNew)
                else:
                    # 这个是别的动态参数， 如果存在接口参数里面 则设为要进行传入的参数
                    if "requestVariable" != key:
                        find_by_exhaustion(variableName, variableValue, paramsCopy, paramsNew)

                create_variable(variableName=variableName, variableValue=variableValue, typeOptions=typeOptions,
                                local_id=local_id, space=key, files=files)

            # requestVariable 是在发起请求时传过来的， 为了让动态参数不存在 请求参数也要加入请求 所有加入一下判断
            if "requestVariable" == key:
                paramsNew = paramsCopy

        try:
            local_id = local_id_copy
            get_variable(paramsNew, local_id, files)
        except Exception as e:
            current_app.logger.error("utils.request_utils.init_params -> 获取参数 报错了 error:{e}->".format(e=repr(e)))

        return paramsNew


# if typeOptions == "interface":
#     paramObj = AlterParams.query.filter(AlterParams.id == variableValue).first()
#     interfaceId = paramObj.interfaceId
#     interfaceObj = AlterInterface.query.filter(AlterInterface.id == interfaceId).first()
#     params = paramObj.params
#     method = paramObj.method
#     datas = paramObj.useDatas
#     headers = paramObj.headers
#     isFormData = paramObj.isFormData
#     general = {
#         "host": interfaceObj.host,
#         "type": interfaceObj.type,
#         "route": interfaceObj.route
#     }
#     # general["host"], general["type"], general["route"]
#     hosts = get_url(g.environment, general)
#
#     # result = __request(method=method, url=hosts["url"] ,isFormData = isFormData, params=json.loads(params),
#     # datas=json.loads(datas),headers=json.loads(headers))[1].json()


def test(tests, resultJson, local_id, files=None):
    """
        断言测试用例
        tests 预期
        resultJson 实际
        返回isError True成功，False断言有错误
    """
    isError = True
    for test in tests:
        actual = ""
        procedures = test[0]["procedures"]
        actualData = resultJson
        for procedure in procedures:
            procedure = procedure["procedure"]
            try:
                actual = actualData[int(procedure) if procedure.isdigit() else procedure]  # 获取实际数据
                actualData = actualData[int(procedure) if procedure.isdigit() else procedure]
            except:
                pass
        asserts = test[0]["asserts"]
        expect = ""
        for assert_result in asserts:
            expect = get_str_dynamic(str(assert_result["assert"]), local_id, files)  # 获取预期数据
            assert_result["assert"] = expect

        current_app.logger.info("utils.request_utils.test -> 实际:" + str(actual) + "，预期: " + expect)

        actual = str(actual)
        expect = str(expect)

        results = test[0]["results"]
        if assertUtils.assertEqual(actual, expect):
            results[0]["result"] = "成功"
            results[0]["type"] = "success"
        else:
            isError = False
            results[0]["result"] = "失败"
            results[0]["type"] = "danger"
    return isError


def run_tests(interfaceParams, rests):
    num = 0
    local_id = rests["local_id"]  # 局部环境变量 Id
    caseId = rests["caseId"]
    environment = rests["environment"]
    projectId = rests["projectId"]
    source = rests["source"]
    userDatas = rests["userDatas"]
    userId = rests["userId"]
    gatherId = rests["gatherId"]
    success_num = 0
    error_num = 0
    amount = 0
    try:
        log_obj = AlterExecuteLog.query.filter(AlterExecuteLog.caseId == caseId).first()
        if log_obj is None:
            db.session.add(
                AlterExecuteLog(caseId=caseId, source=source, success_num=success_num, error_num=error_num,
                                amount=amount, log_type=0, projectId=projectId, gatherId=gatherId))
        else:
            success_num = log_obj.success_num
            error_num = log_obj.error_num
            amount = log_obj.amount
            log_obj.gatherId = log_obj.gatherId + "," + str(gatherId)
        db.session.commit()
    except Exception as e:
        current_app.logger.error("utils.request_utils.run_tests -> 插入AlterExecuteLog： 失败 error:{e}->".format(e=repr(e)))

    for interfaceParam in interfaceParams:
        interfaceId = interfaceParam.interfaceId
        interfaceObj = AlterInterface.query.filter(AlterInterface.id == interfaceId).first()

        params = json.loads(interfaceParam.params)
        headers = json.loads(interfaceParam.headers)
        method = interfaceParam.method
        isFormData = interfaceParam.isFormData
        rests = json.loads(interfaceParam.rests)

        before = {"params": params, "headers": headers, "paramsId": interfaceParam.id, "projectId": projectId}

        general = {
            "host": interfaceObj.host,
            "type": interfaceObj.type,
            "route": interfaceObj.route
        }
        try:
            hosts = get_url(environment, general)
        except Exception as e:
            current_app.logger.error("utils.request_utils.run_tests -> 环境转换失败 -> error:{e}".format(e=repr(e)))
            return restful.params_error(message="请选择环境")

        url = hosts["url"]
        rests["caseId"] = caseId
        rests["local_id"] = local_id
        rests["interceptor"] = environment
        rests["flows"] = interfaceParam.flows  # 存储主要的flows里面的信息
        rests["interfaceName"] = interfaceParam.describe  # 用例名
        before["userId"] = userId

        initial_tests = mongo.db.initialTests.find({"paramsId": interfaceParam.id})
        initial = json.loads(json_util.dumps(initial_tests))
        rests["paramsInitialTests"] = []
        if len(initial) != 0:
            rests["paramsInitialTests"] = list(initial[0]["initialTests"])

        dynamic_variable = mongo.db.dynamicVariable.find({"paramsId": interfaceParam.id})
        interface_dynamic = json.loads(json_util.dumps(dynamic_variable))
        if len(interface_dynamic) == 0:
            interface_dynamic = []
        else:
            interface_dynamic = list(interface_dynamic[0]["dynamicVariable"])

        dynamics = {
            "taskVariable": interfaceParam.flows["flowUseDatas"],
            "userVariable": json.loads(userDatas),
            "interfaceDynamic": interface_dynamic
        }
        rests["dynamics"] = dynamics

        rests["files"] = interfaceParam.files

        result = __request(method=method, url=url, isFormData=isFormData, before=before, rests=rests, isFlow=True)
        amount += 1
        if result[2] == 0:
            success_num += 1
        else:
            error_num += 1
        num += 1

    if local_id in taskVariableDict:
        del taskVariableDict[local_id]

    return {
        "success_num": success_num,
        "error_num": error_num,
        "amount": amount
    }


def init_before_sql(beforeSqls, interceptor):
    db_test = gat_db_object(interceptor)

    if isinstance(beforeSqls, str):
        current_app.logger.info(
            "utils.request_utils.init_before_sql -> sql:{sql} , interceptor: {interceptor}".format(sql=beforeSqls,
                                                                                                   interceptor=interceptor))
        db_test.execute_sql(beforeSqls, None)
    else:
        for sql in beforeSqls:
            current_app.logger.info(
                "utils.request_utils.init_before_sql -> sql:{sql} , interceptor: {interceptor}".format(sql=sql,
                                                                                                       interceptor=interceptor))
            db_test.execute_sql(sql, None)


def init_before_redis(beforeRedis,interceptor):
    """
    {
    "" 咱只支持删除
    }
    :param beforeRedis:
    :return:
    """
    redis_db = get_redis_object(interceptor)
    if isinstance(beforeRedis, str):
        if beforeRedis == "":
            return
        redis_db.delete(beforeRedis)
    else:
        for redis in beforeRedis:
            if redis == "":
                continue
            redis_db.delete(redis)


def init_after(assertObj, interceptor, local_id=None, files=None):
    sql = assertObj["sql"]
    if sql == '':
        return assertObj, True
    expectDatas = assertObj["sqlsTableDatas"]

    try:
        db_test = gat_db_object(interceptor)

        actualDats, actualCols = db_test.fetchall_new(sql)
        assertObj["sqlCols"] = actualCols
    except Exception as e:
        current_app.logger.error(
            "utils.request_utils.init_after -> Sql执行失败 sql:{sql} , interceptor:{interceptor}, error:{e}".format(sql=sql,
                                                                                                                interceptor=interceptor,
                                                                                                                e=repr(
                                                                                                                    e)))
        return assertObj, False

    if assertUtils.assertEqualDict(expectDatas, actualDats, local_id=local_id, files=files):
        current_app.logger.info(
            "utils.request_utils.init_after -> 断言SQL成功 预期: actualDats: {expectDatas} 实际: actualDats: {actualDats}".format(
                expectDatas=expectDatas, actualDats=actualDats))

        return assertObj, True
    else:
        current_app.logger.debug(
            "utils.request_utils.init_after -> 断言SQL失败 预期: actualDats: {expectDatas} 实际: actualDats: {actualDats}".format(
                expectDatas=expectDatas, actualDats=actualDats))
        return assertObj, False


def get_url(environment, general):
    isReplace = False
    host, type, route = general["host"], general["type"], general["route"]

    if host.find("{") != -1:
        isReplace = True
        host = str(host)[2:int(host.index("}"))]

    hosts = AlterHost.query.filter(
        db.and_(AlterHost.environmentId == environment, AlterHost.name == host)
    ).first()
    if environment in [7, 8]:
        type = "http://"
    if isReplace:
        if hosts is None:
            current_app.logger.debug("utils.request_utils.get_url -> 请选择环境")
            raise RuntimeError("请选择环境")
        hostType = type.lower() + hosts.host
    else:
        hostType = type.lower() + host

    url = hostType + route
    return {
        "url": url,
        "host": hostType
    }


def dict_format_str(data):
    return str(json.dumps(obj=data, ensure_ascii=False))


# def format_sql(sql):

def dynamic_transition(dynamic, content):
    """
    dynamic 动态参数 renterGetAndReturnCarDTO.getKM, renterGetAndReturnCarDTO.0.getKM
    动态参数转 字典
    :return:
    """
    variableName = dynamic.split(".")
    result = {}
    for variable in variableName:
        result
        variableValue = content[variable]
