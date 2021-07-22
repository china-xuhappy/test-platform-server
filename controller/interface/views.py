#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @File  : views.py
# @Author: kaixin.xu
# @Date  : 2020/3/17
# @Desc  : 用户相关接口
from bson import json_util
from flask import Blueprint, request, g, current_app, make_response, send_from_directory
from flask_restful import Api, Resource, marshal_with, reqparse, fields

interface = Blueprint('interface', __name__, url_prefix='/interface')
from utils import restful
from exts import db, mongo
from flask import current_app

api = Api(interface)
from controller.project.models import AlterProject, \
    AlterInterface, AlterParams, \
    AlterFlow, AlterTemplate, AlterUser, AlterCatalogue, AlterFiles
import json
from utils.request_utils import __request, get_url
from utils.variable_utils import requestVariableDict, params_to_dynamic
from sqlalchemy import and_
import time
from utils.curl_parse import charles_to_json, browser_to_json

"""
添加接口参数模板
"""


@interface.route("/addTemplate", methods=['POST'])
def add_template():
    parser = reqparse.RequestParser()
    parser.add_argument('templateParams', required=True, type=dict)
    args = parser.parse_args()
    templateParams = str(json.dumps(obj=args["templateParams"], ensure_ascii=False))

    db.session.add(AlterTemplate(templateParams=templateParams))
    db.session.commit()

    return restful.success()


@interface.route("/searchInterface")
def search_interface():
    interfaceName = request.args.get('interfaceName')
    paramsObj = AlterParams.query.filter(
        and_(AlterParams.describe.like("%" + interfaceName + "%"), AlterParams.is_delete == 0)).first()
    if paramsObj is None:
        return restful.params_error("未查询到.")

    sonCatalogueId = paramsObj.catalogueId
    catalogueObj = AlterCatalogue.query.filter(AlterCatalogue.id == sonCatalogueId).first()
    if catalogueObj is None:
        return restful.params_error("未查询到.")

    return restful.success(data={
        "sonCatalogueId": sonCatalogueId,
        "catalogueId": catalogueObj.catalogueId,
        "projectId": catalogueObj.projectId,
        "paramsObj": {
            "paramsId": paramsObj.id
        }
    })


@interface.route("/getIterfaces")
def get_iterfaces():
    projectId = request.args.get('projectId')

    results = []
    interfaces = AlterInterface.query.order_by(db.desc(AlterInterface.id)).filter(
        and_(AlterInterface.is_delete == 0, AlterInterface.projectId == projectId)).all()

    for interface in interfaces:
        param = interface.param
        if len(param) != 0:

            dynamic_variable = mongo.db.dynamicVariable.find({"paramsId": param[0].id})
            dynamic = json.loads(json_util.dumps(dynamic_variable))
            if len(dynamic) == 0:
                dynamic = [{"variableName": "", "variableValue": [""], "typeOptions": "String"}]
            else:
                dynamic = list(dynamic[0]["dynamicVariable"])

            params_desc = mongo.db.paramsDesc.find({"paramsId": param[0].id})
            params_desc_dynamic = json.loads(json_util.dumps(params_desc))
            if len(params_desc_dynamic) != 0:
                params_desc_dynamic = list(params_desc_dynamic[0]["paramsDesc"])

            initial_tests = mongo.db.initialTests.find({"paramsId": param[0].id})
            initial = json.loads(json_util.dumps(initial_tests))
            if len(initial) != 0:
                initial = list(initial[0]["initialTests"])

            results.append({
                "interfaceId": interface.id,
                "value": param[0].describe,
                "paramId": param[0].id,
                "dynamicVariable": dynamic,
                "initialTests": initial,
                "paramsDesc": params_desc_dynamic if params_desc_dynamic is not None else ""
            })
    return restful.success(data=results)


# 请求接口
@interface.route("/requestInterface", methods=['POST'])
def request_interface():
    parser = reqparse.RequestParser()
    parser.add_argument('general', required=True, type=dict)  # 基本信息，请求类型Method(POST,GET) ,请求地址host
    parser.add_argument('rests', required=False, type=dict)  # 其他配置
    parser.add_argument('environment', required=False, type=int)
    parser.add_argument('userId', required=False, type=int)  # 用户Id
    parser.add_argument('catalogueId', required=False, type=int)  # 目录Id
    parser.add_argument('before', required=False, type=dict)  # 前置执行的，params,headers,datas 比如SQL，动态参数，保存返回结果
    parser.add_argument('after', required=False, type=dict)  # 后置执行的 tests 比如sql , 数据断言，sql断言
    parser.add_argument('initialTests', required=False, type=list)  # 初始化数据
    args = parser.parse_args()
    initialTests = args["initialTests"]
    general = args["general"]
    method = general["method"]
    isFormData = general["isFormData"]
    before = args["before"]
    rests = args["rests"]
    g.environment = args["environment"]
    try:
        hosts = get_url(g.environment, general)
    except Exception as e:
        current_app.logger.error(
            "interface.views.request_interface --> URL -> 环境转换错误 environment:{environment} , e:{e}".format(
                environment=g.environment, e=repr(e)))
        return restful.params_error(message="请选择环境")

    # 生成locust 文件
    # createLocust(hosts["host"],method.lower(),general["route"],",json="+str(json.dumps(obj=before["params"], ensure_ascii=False)))

    url = hosts["url"]

    caseId = "AT" + str((int(round(time.time() * 1000))))
    rests["caseId"] = caseId

    userObj = AlterUser.query.filter(AlterUser.id == args["userId"]).first()
    dynamics = {
        "requestVariable": before["dynamicVariable"],
        "userVariable": json.loads(userObj.useDatas)
    }

    before["userId"] = args["userId"]
    rests["dynamics"] = dynamics
    rests["paramsInitialTests"] = initialTests
    rests["flowName"] = ""
    rests["interfaceName"] = ""
    rests["interceptor"] = args["environment"]
    files = []
    for file in AlterFiles.query.filter(
            and_(AlterFiles.project_id == before["projectId"], AlterFiles.is_delete == 0)).all():
        files.append(file.file_name)
    rests["files"] = files

    result = __request(method, url, isFormData, before, rests=rests)  # 请求接口

    # 请求完 清空动态变量， 预防影响别的请求
    requestVariableDict.clear()

    if result[0] != 200:
        return restful.params_error(message=result[1])
    else:
        caseId = result[1]
        return restful.success(data={
            "interfaceData": result[3],
            # "tests": after["tests"],
            # "isError": 0 if isError else 1,
            "caseId": caseId
        }, message="请求成功")


# 获取接口 动态参数
@interface.route("/getInterfaceDatas")
def get_interface_datas():
    flowId = request.args.get('flowId')
    flow = AlterFlow.query.filter(AlterFlow.id == flowId).first()
    run_results = mongo.db.flowParameters.find_one({"flowId": flow.id})
    data = json.loads(json_util.dumps(run_results))
    dynamicVariables = data["dynamicVariable"]
    return restful.success(data={
        "dynamicVariable": dynamicVariables,
        "rests": flow.rests,
        "initialTests": data["initialTests"],
        "flowName": flow.name
    })


@interface.route("/getInterfaceMsg")
def get_interface_msg():
    """
    获取接口信息
    :return:
    """
    paramsId = request.args.get('paramsId')

    params = AlterParams.query.filter(AlterParams.id == paramsId).first()
    interface = params.interface
    dynamic_variable = mongo.db.dynamicVariable.find({"paramsId": params.id})
    dynamic = json.loads(json_util.dumps(dynamic_variable))
    if len(dynamic) == 0:
        dynamic = None
    else:
        dynamic = list(dynamic[0]["dynamicVariable"])

    params_desc = mongo.db.paramsDesc.find({"paramsId": params.id})
    params_desc_dynamic = json.loads(json_util.dumps(params_desc))
    if len(params_desc_dynamic) != 0:
        params_desc_dynamic = str(params_desc_dynamic[0]["paramsDesc"])

    initial_tests = mongo.db.initialTests.find({"paramsId": params.id})
    initial = json.loads(json_util.dumps(initial_tests))
    initialTests = None
    if len(initial) != 0:
        initialTests = list(initial[0]["initialTests"])
        if "beforeRedis" not in initialTests[0]:
            initialTests[0]["beforeRedis"] = [""]

    return restful.success(data={
        "id": params.id,
        "projectId": interface.projectId,
        "interfaceId": interface.id,
        "describe": params.describe,
        "params": params.params,
        "headers": params.headers,
        "dynamicVariable": dynamic,
        "initialTests": initialTests,
        "method": params.method,
        "isFormData": params.isFormData,
        "rests": params.rests,
        "sqls": params.sqls,
        "interface": {
            "url": interface.url,
            "method": interface.method,
            "type": interface.type,
            "host": interface.host,
            "route": interface.route
        },
        "paramsDesc": params_desc_dynamic if params_desc_dynamic is not None else ""
    })


# 获取接口 接口报文 操作
@interface.route("/getInterfaceParameters")
def get_interface_parameters():
    flowId = request.args.get('flowId')
    flow = AlterFlow.query.filter(AlterFlow.id == flowId).first()
    return restful.success(data={
        "Parameters": flow.parameters
    })


# 接口用的
class InterfaceOperation(Resource):
    resource_fields = {
        "id": fields.Integer,
        "userId": fields.Integer,
        "projectName": fields.String
    }

    def post(self):  # add
        parser = reqparse.RequestParser()
        parser.add_argument('general', required=True, type=dict)
        parser.add_argument('catalogueId', required=True, type=int)
        parser.add_argument('projectId', required=True, type=int)
        parser.add_argument('interfaceId', required=False, type=int)
        parser.add_argument('interfaceName', required=False, type=str)
        parser.add_argument('params', required=True, type=dict)
        parser.add_argument('paramsDesc', required=False, type=str)
        parser.add_argument('flag', required=False, type=int)
        parser.add_argument('headers', required=False, type=list)
        parser.add_argument('dynamicVariable', required=False, type=list)  # 动态数据
        parser.add_argument('initialTests', required=False, type=list)  # 初始化数据
        parser.add_argument('rests', required=False, type=dict)  # 其他配置
        parser.add_argument('typeStatus', required=True, type=int)  # 0 添加 1修改 2删除

        parser.add_argument('curlToJson', required=False, type=str)  #
        parser.add_argument('curlType', required=False, type=str)  # charles brow

        args = parser.parse_args()
        type_status = args["typeStatus"]
        interface_id = args["interfaceId"]
        interface = AlterInterface.query.filter(AlterInterface.id == interface_id).first()
        param = AlterParams.query.filter(AlterParams.interfaceId == interface_id).first()

        if type_status == 2 and interface is not None:  # 删除
            interface.is_delete = 1
            param.is_delete = 1
            db.session.commit()
            return restful.success("删除成功")

        # 初始化
        params = {}
        headers = [{"headersKey": "", "headersValue": ""}]
        # method = "GET"
        # type = "HTTP://"
        # host, route, url = "", "", ""
        general = args["general"]
        type = general["type"]
        host = general["host"]
        route = general["route"]
        url = general["url"]
        method = general["method"]
        flag = args["flag"]
        if flag is None:
            flag = 1

        interfaceName = args["interfaceName"]
        paramsDesc = args["paramsDesc"]
        if type_status == 0:
            curlToJson = args["curlToJson"]
            curlType = args["curlType"]
            result = None
            if "browser" == curlType and curlToJson != '':
                result = browser_to_json(curlToJson.replace("\'", "\""))

            if "charles" == curlType and curlToJson != '':
                result = charles_to_json(curlToJson)

            if curlType != '' and result is not None:
                headers = result["headers"]
                headers_list = []
                for header in headers:
                    headers_list.append({
                        "headersKey": header,
                        "headersValue": headers[header]
                    })
                headers = headers_list
                params = result["params"]
                url = result["url"]
                method = result["method"]
                type = result["type"].upper() + "://"
                host = result["host"]
                route = result["route"]

        try:
            params = str(json.dumps(obj=params, ensure_ascii=False))
            rests = str(json.dumps(obj=args["rests"], ensure_ascii=False))

            headers = str(json.dumps(obj=headers, ensure_ascii=False))
            # initialTests = str(json.dumps(obj=args["initialTests"], ensure_ascii=False))
            sqls = str(json.dumps(obj=args["rests"]["sqls"], ensure_ascii=False))
        except Exception as e:
            print(repr(e))
            current_app.logger.error("interface.views.InterfaceOperation.post --> JSON转换错误 -> 参数不是json")

            return restful.params_error("参数不是json")

        dynamicVariable = args["dynamicVariable"]
        projectId = args["projectId"]

        if type_status == 0:  # 添加
            dynamicVariable = [{'required': False, 'typeOptions': 'String', 'variableName': "", 'variableValue': ""}]
            interface = AlterInterface(url=url, type=type, host=host, route=route,
                                       method=method, projectId=projectId, name=interfaceName)
            db.session.add(interface)
            db.session.commit()

            interface_id = interface.id  # 添加到数据库 取出接口id

            params = json.loads(params)
            params_to_dynamic(params, dynamicVariable)
            params = str(json.dumps(obj=params, ensure_ascii=False))

            params = AlterParams(catalogueId=args["catalogueId"], interfaceId=interface_id,
                                 params=params, headers=headers, describe=interfaceName, method=method,flag=flag)
            db.session.add(params)
            db.session.commit()
            mongo.db.dynamicVariable.insert_one(
                {
                    "dynamicVariable": dynamicVariable,
                    "paramsId": params.id,
                    "interfaceId": interface.id
                }
            )

            mongo.db.paramsDesc.insert_one(
                {
                    "paramsDesc": paramsDesc,
                    "paramsId": params.id,
                    "interfaceId": interface.id
                }
            )

        elif type_status == 1 and interface is not None:  # 修改
            params = args["params"]
            params_to_dynamic(params, dynamicVariable)

            try:
                params = str(json.dumps(obj=params, ensure_ascii=False))
            except Exception as e:
                print(repr(e))
                current_app.logger.error("interface.views.InterfaceOperation.post --> params JSON转换错误 -> 参数不是json")
                return restful.params_error("参数不是json")

            headers = args["headers"]
            try:
                headers = str(json.dumps(obj=headers, ensure_ascii=False))
            except Exception as e:
                print(repr(e))
                current_app.logger.error("interface.views.InterfaceOperation.post --> headers JSON转换错误 -> 参数不是json")
                return restful.params_error("参数不是json")
            interface.id = interface_id
            interface.url = url
            interface.type = type
            interface.host = host
            interface.route = route
            interface.isFormData = general["isFormData"]
            interface.projectId = projectId

            param.catalogueId = args["catalogueId"]
            param.interfaceId = args["interfaceId"]
            param.params = params
            param.headers = headers
            if interfaceName != "":
                param.describe = interfaceName
            param.method = method
            param.isFormData = general["isFormData"]
            param.rests = rests
            # param.useDatas = datas
            # param.initialTests = initialTests
            param.sqls = sqls

            initialTests = args["initialTests"]
            initial_tests = mongo.db.initialTests.find({"paramsId": param.id})
            initial = json.loads(json_util.dumps(initial_tests))
            if len(initial) == 0:
                mongo.db.initialTests.insert_one(
                    {
                        "initialTests": initialTests,
                        "paramsId": param.id,
                        "interfaceId": interface.id
                    }
                )
            else:
                mongo.db.initialTests.update(
                    {
                        "paramsId": param.id
                    },
                    {
                        "$set": {
                            "initialTests": initialTests
                        }
                    }
                )

            dynamic_variable = mongo.db.dynamicVariable.find({"paramsId": param.id})
            dynamic = json.loads(json_util.dumps(dynamic_variable))
            if len(dynamic) == 0:
                mongo.db.dynamicVariable.insert_one(
                    {
                        "dynamicVariable": dynamicVariable,
                        "paramsId": param.id,
                        "interfaceId": interface.id
                    }
                )
            else:
                mongo.db.dynamicVariable.update(
                    {
                        "paramsId": param.id
                    },
                    {
                        "$set": {
                            "dynamicVariable": dynamicVariable
                        }
                    }
                )

            params_desc_init = mongo.db.paramsDesc.find({"paramsId": param.id})
            params_desc_dynamic = json.loads(json_util.dumps(params_desc_init))
            if len(params_desc_dynamic) == 0:
                mongo.db.paramsDesc.insert_one(
                    {
                        "paramsDesc": paramsDesc,
                        "paramsId": param.id,
                        "interfaceId": interface.id
                    }
                )
            else:
                mongo.db.paramsDesc.update(
                    {
                        "paramsId": param.id
                    },
                    {
                        "$set": {
                            "paramsDesc": paramsDesc
                        }
                    }
                )
        db.session.commit()
        return restful.success("保存成功")

    @marshal_with(resource_fields)
    def get(self):  # get
        return AlterProject.query.filter(AlterProject.userId == 1).all()


api.add_resource(InterfaceOperation, '/interfaceOperation')

# @project.route("/addInterface",methods=['POST'])
# def add_interface():
#     print(request.json)
