"""
用例相关接口
"""
import json
import os
import time

from bson import json_util
from flask import Blueprint, jsonify, g, render_template, request
from flask_restful import Api, Resource, marshal_with, reqparse, fields

import config
from controller.project.models import AlterProject
from ui_controller.case.models import UiCase, UiStep
from ui_controller.element.models import UiElements, UiActivitys
from ui_controller.suite.models import UiSuite, UiDevices
from ui_controller.suite.views import get_connect_devices
from utils.appium_tool import get_user_ip, execute_step, start_appium
from utils.excel_utils import import_ui_case

ui_case = Blueprint('ui_case', __name__, url_prefix='/ui_case')
from exts import db, mongo
from datetime import datetime

api = Api(ui_case)
from utils import restful
from sqlalchemy import or_, and_, func

# class Operation(object):
#     Input = (0, "输入")
#     Click = (1, "点击")
#
#     def __init__(self, key):
#         self.key = key
#
#     @property
#     def code(self):
#         return getattr(self, self.key).keys()[0]
#
#     @property
#     def value(self):
#         return getattr(self, self.key).values()[0]


operations = [
    {
        "operationName": "点击",
        "operationId": 0
    },
    {
        "operationName": "输入",
        "operationId": 1
    },
    {
        "operationName": "返回",
        "operationId": 9
    },
    {
        "operationName": "切换界面",
        "operationId": 8
    },
    {
        "operationName": "断言跳转",  # 断言跳转
        "operationId": 6
    },
    {
        "operationName": "断言出现",  # 断言出现某个元素
        "operationId": 7
    },
    {
        "operationName": "左滑",
        "operationId": 2
    },
    {
        "operationName": "右滑",
        "operationId": 3
    },
    {
        "operationName": "上滑",
        "operationId": 4
    },
    {
        "operationName": "下滑",
        "operationId": 5
    },

]

caseCols = [
    {
        "label": "序号"
    },
    {
        "label": "用例标题"
    },
    {
        "label": "所属项目"
    },
    {
        "label": "描述信息"
    },
    {
        "label": "创建时间"
    }
]

devicesCols = [
    {
        "label": "设备名"
    },
    {
        "label": "IP"
    },
    {
        "label": "端口号(Port)"
    },
    {
        "label": "端口号(APort)"
    },
    {
        "label": "端口号(BPort)"
    },
    {
        "label": "是否连接"
    },
    {
        "label": "设备状态"
    },
    {
        "label": "设备描述"
    }
]


@ui_case.route("/getUiCases")
def get_ui_cases():
    """
    专门给套件用的，获取所有用例和已有用例
    :return:
    """
    projectId = request.args.get('projectId')
    suiteId = request.args.get('suiteId')

    result = {
        "cases": [],
        "caseIds": []
    }
    if projectId is not None:
        cases = UiCase.query.filter(and_(UiCase.projectId == projectId, UiCase.is_delete == 0)).all()
    else:
        cases = UiCase.query.filter(UiCase.is_delete == 0).all()
    suite = UiSuite.query.filter(and_(UiSuite.id == suiteId)).first()

    caseIds = suite.caseIds
    if caseIds is not None and caseIds != "":
        caseIds = str(caseIds).split(",")
    else:
        caseIds = []

    caseIds = list(map(eval, caseIds))
    for case in cases:
        result["cases"].append({
            "key": case.id,
            "label": case.case_name
        })
    result["caseIds"] = caseIds
    return restful.success(data=result)


class UICaseOperation(Resource):
    def post(self):
        data = request.get_data()
        json_data = json.loads(data.decode("utf-8"))
        case_name = json_data["caseName"]
        describe = json_data["describe"]
        projectId = json_data["projectId"]

        db.session.add(UiCase(case_name=case_name, describe=describe, projectId=projectId))
        db.session.commit()
        return restful.success()

    def get(self):  # get
        projectId = request.args.get('projectId')
        result = {
            "cases": []
        }
        if projectId is not None:
            cases = UiCase.query.filter(and_(UiCase.projectId == projectId, UiCase.is_delete == 0)).all()
        else:
            cases = UiCase.query.filter(UiCase.is_delete == 0).all()

        for case in cases:
            case_name = case.case_name
            create_time = case.create_time
            describe = case.describe
            project = AlterProject.query.filter(AlterProject.id == case.projectId).first()

            result["cases"].append({
                "序号": case.id,
                "用例标题": case_name,
                "所属项目": project.projectName,
                "描述信息": describe,
                "创建时间": create_time.strftime("%Y-%m-%d %H:%M:%S"),
                "caseId": case.id,
                "caseName": case_name,
                "projectName": project.projectName,
                "describe": describe
            })

        result["caseCols"] = caseCols
        return restful.success(data=result)


api.add_resource(UICaseOperation, '/uICaseOperation')


class UIStepOperation(Resource):
    def post(self):
        data = request.get_data()
        json_data = json.loads(data.decode("utf-8"))
        case_name = json_data["caseName"]
        describe = json_data["describe"]
        caseId = json_data["caseId"]
        stepDatas = json_data["stepDatas"]
        print(stepDatas)
        case = UiCase.query.filter(and_(UiCase.id == caseId)).first()
        case.case_name = case_name
        case.describe = describe

        sorts = 999
        stepOther = db.session.query(func.min(UiStep.sort).label('sort')).filter(
            db.and_(UiStep.caseId == caseId, UiStep.is_delete == 0)).first()

        if stepOther.sort is not None:
            sorts = int(stepOther.sort) - 1
        sorts += 1
        for stepData in stepDatas:
            print(stepData)
            content = None
            elementId = None
            activityId = None

            operation = stepData["operation"]

            if operation != "左滑" and operation != "右滑" and operation != "上滑" and operation != "下滑" and operation != "返回":
                activityId = stepData["activityId"]
                if activityId is None:
                    return restful.params_error(message="页面(Activity) 未选择")

                if operation != "断言跳转" and operation != "切换界面":
                    elementId = stepData["elementId"]
                    if elementId is None:
                        return restful.params_error(message="元素(Element) 未选择")

                if operation == "输入":
                    content = stepData["content"]
                    if content == "":
                        return restful.params_error(message="内容未输入")

            if "ID" in stepData:
                id = stepData["ID"]
                step = UiStep.query.filter(UiStep.id == id).first()
                step.elementId = elementId
                step.activityId = activityId
                step.operation = operation
                step.content = content
                step.update_time = datetime.now()
            else:
                sorts -= 1
                db.session.add(UiStep(operation=operation, caseId=caseId, elementId=elementId, activityId=activityId,
                                      content=content, sort=sorts))

        db.session.commit()
        return restful.success(message="保存成功")

    def get(self):  # get
        caseId = request.args.get('caseId')
        result = {
            "steps": [],
            "operations": operations,
            "activitys": [],
            "elements": []
        }
        steps = UiStep.query.order_by(db.desc(UiStep.sort)).filter(
            and_(UiStep.caseId == caseId, UiStep.is_delete == 0)).all()
        activitys = UiActivitys.query.all()
        for activity in activitys:
            result["activitys"].append({
                "activityName": activity.activity_name,
                "activityId": activity.id
            })
        for step in steps:
            result["elements"] = []
            operation = step.operation
            caseId = step.caseId
            elementId = step.elementId
            content = step.content
            activityId = step.activityId

            element = UiElements.query.filter(UiElements.id == elementId).first()
            element_name = ""
            if element is not None:
                element_name = element.element_name

                elements = UiElements.query.filter(
                    and_(UiElements.activityId == activityId, UiElements.is_delete == 0)).all()
                for element in elements:
                    result["elements"].append({
                        "element_name": element.element_name,
                        "id": element.id
                    })

            isInput = False
            isElement = True
            isActivity = True

            if operation == "输入":
                isInput = True
            if operation == "断言跳转" or operation == "切换界面":
                isElement = False

            if operation == "左滑" or operation == "右滑" or operation == "上滑" or operation == "下滑" or operation == "返回":
                isActivity = False
                isElement = False

            result["steps"].append({
                "ID": step.id,
                "operation": operation,
                "activity_name": elementId,
                "element_name": element_name,
                "content": content,
                "caseId": caseId,
                "elementId": elementId,
                "activityId": activityId,
                "isInput": isInput,
                "isElement": isElement,
                "isActivity": isActivity,
                "activitys": result["activitys"],
                "elements": result["elements"]
            })
        return restful.success(data=result)


api.add_resource(UIStepOperation, '/uiStepOperation')


@ui_case.route("/deleteStep", methods=['POST'])
def delete_step():
    """
    删除步骤
    :return:
    """
    ip = get_user_ip(request)
    data = request.get_data()
    json_data = json.loads(data.decode("utf-8"))
    stepId = json_data["stepId"]  # 步骤ID
    step = UiStep.query.filter(UiStep.id == stepId).first()
    step.is_delete = 1
    db.session.commit()

    return restful.success()


@ui_case.route("/delectCase", methods=['POST'])
def delect_case():
    """
    删除用例
    :return:
    """
    ip = get_user_ip(request)
    data = request.get_data()
    json_data = json.loads(data.decode("utf-8"))
    caseId = json_data["caseId"]  # 步骤ID
    case = UiCase.query.filter(UiCase.id == caseId).first()
    case.is_delete = 1
    db.session.commit()

    return restful.success()


@ui_case.route("/runSteps", methods=['POST'])
def run_steps():
    """
    执行某个步骤，
    调试用的。
    :return:
    """
    ip = get_user_ip(request)
    data = request.get_data()
    json_data = json.loads(data.decode("utf-8"))
    device = json_data["device"]  # 设备名
    steps = json_data["steps"]  # 选择的步骤
    isAgain = json_data["isAgain"]

    deviceObj = UiDevices.query.filter(UiDevices.device == device).first()  # 获取启动的设备
    if int(deviceObj.is_run) == 1:
        return restful.params_error("设备正在执行用例..")

    if int(deviceObj.status) == 0:
        # 机器未启动
        if not start_appium(**{"deviceObj": deviceObj, "ip": ip, "isAgain": isAgain}):
            return restful.server_error()

    caseIdCode = "UI" + str((int(round(time.time() * 1000))))
    for step in steps:
        content, activityId, elementId, element_name, element_type, element_path, content = None, None, None, None, None, None, None
        operation = step["operation"]
        if "activityId" in step:
            activityId = step["activityId"]

        if "elementId" in step:
            elementId = step["elementId"]

        if "content" in step:
            content = step["content"]

        if elementId is not None and elementId != "":
            element = UiElements.query.filter(UiElements.id == elementId).first()
            element_name = element.element_name
            element_type = element.element_type
            element_path = element.element_path

        activity_name = None
        activity_path = None
        activityObj = UiActivitys.query.filter(UiActivitys.id == activityId).first()
        if activityObj is not None:
            activity_name = activityObj.activity_name
            activity_path = activityObj.activity_path

        kwargs = {
            "element": {
                "element_name": element_name,
                "element_type": element_type,
                "element_path": element_path,
                "content": content
            },
            "operation": operation,
            "ip": ip,
            "activityObj": {
                "activityId": activityId,
                "activityName": activity_name,
                "activityPath": activity_path
            },
            "elementId": elementId,
            "caseName": "",
            "caseTitle": "",
            "caseId": caseIdCode,
            "deviceObj": {
                "device_port": deviceObj.device_port,
                "device_bp": deviceObj.device_bp,
                "deviceName": deviceObj.device
            }
        }

        result = execute_step(**kwargs)
        if result[0]["status"] == 500:  # 强制关闭服务，无法识别到 但是数据库状态没变。 在执行步骤时判断是否变了。 然后在变状态
            device = UiDevices.query.filter(UiDevices.device == device).first()
            device.status = 0
            db.session.commit()
            return restful.unauth_error(message="设备未启动，请重新执行..")

        if result[1] == 1:
            return restful.unauth_error(message="断言失败")

    return restful.success(message="执行成功")


class UIDevicesOperation(Resource):
    """
    管理设备的api
    """

    def post(self):
        ip = get_user_ip(request)
        data = request.get_data()
        json_data = json.loads(data.decode("utf-8"))
        deviceName = json_data["deviceName"]
        device_port = json_data["devicePort"]
        device_bp = json_data["deviceBp"]
        if "deviceId" in json_data:
            deviceId = json_data["deviceId"]

        describe = json_data["describe"]
        statusType = json_data["type"]  # 0新增， 1修改
        if statusType == 0:
            device = UiDevices.query.filter(and_(UiDevices.device == deviceName, UiDevices.ip == ip)).first()
            if device is not None:
                return restful.params_error(message="设备已经存在")

            db.session.add(
                UiDevices(device=deviceName, ip=ip, device_port=device_port, device_bp=device_bp, describe=describe))
        elif statusType == 1:
            device = UiDevices.query.filter(UiDevices.id == deviceId).first()
            device.device = deviceName
            device.device_port = device_port
            device.device_bp = device_bp
            device.describe = describe
        db.session.commit()
        return restful.success()

    def get(self):  # get
        ip = get_user_ip(request)
        result = {
            "devices": []
        }
        # devices = UiDevices.query.filter(UiDevices.ip == ip).all()
        devices = UiDevices.query.all()
        devices_usable = []
        try:
            devices_usable = get_connect_devices(ip)
        except Exception as e:
            print(repr(e))

        for device in devices:
            deviceName = device.device
            describe = device.describe
            create_time = device.create_time
            device_port = device.device_port
            device_bp = device.device_bp
            status = device.status

            result["devices"].append({
                "设备名": deviceName,
                "端口号(Port)": device_port,
                "端口号(APort)": 0,
                "端口号(BPort)": device_bp,
                "是否连接": "已连接" if deviceName in devices_usable else "未连接",
                "设备状态": "待运行" if status == '0' else "正在执行",
                "创建时间": create_time.strftime("%Y-%m-%d %H:%M:%S"),
                "设备描述": describe,
                "IP": device.ip,
                "deviceId": device.id,
                "device_port": device_port,
                "deviceName": deviceName,
                "device_bp": device_bp,
                "describe": describe
            })

        result["devicesCols"] = devicesCols
        return restful.success(data=result)


api.add_resource(UIDevicesOperation, '/uiDevicesOperation')


@ui_case.route("/importStep/", methods=['POST'])
def import_step():
    """
    导入步骤
    :return:
    """
    file = request.files['file']
    projectId = request.form['projectId']
    print(file)
    case_url = os.path.join(config.UI_CASE_UPLOAD_FOLDER, file.filename)
    print(case_url)
    import_ui_case(file.read(), projectId)

    return restful.success()