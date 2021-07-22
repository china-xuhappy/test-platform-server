"""
用例相关接口
"""
import json
import time

from bson import json_util
from flask import Blueprint, jsonify, g, render_template, request
from flask_restful import Api, Resource, marshal_with, reqparse, fields

from controller.project.models import AlterProject, AlterExecuteLog
from ui_controller.case.models import UiCase, UiStep
from ui_controller.element.models import UiElements, UiActivitys
from ui_controller.suite.models import UiSuite, UiDevices
from utils.appium_tool import get_user_ip, execute_step, start_appium

ui_suite = Blueprint('ui_suite', __name__, url_prefix='/ui_suite')
from exts import db, mongo
from datetime import datetime

api = Api(ui_suite)
from utils import restful
from sqlalchemy import or_, and_
import requests

suiteCols = [
    {
        "label": "序号"
    },
    {
        "label": "套件名称"
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


class UiSuiteOperation(Resource):
    """
    Ui自动化
    套件
    """

    def post(self):
        data = request.get_data()
        json_data = json.loads(data.decode("utf-8"))
        suite_name = json_data["suiteName"]
        describe = json_data["describe"]
        projectId = 0
        if "projectId" in json_data:
            projectId = json_data["projectId"]

        caseValue = json_data["caseValue"]
        suiteId = json_data["suiteId"]
        suite = UiSuite.query.filter(UiSuite.id == suiteId).first()
        if suite is None:
            db.session.add(UiSuite(suite_name=suite_name, describe=describe, projectId=projectId))
        else:
            caseIds = None
            if caseValue is not None and caseValue != "":
                caseIds = ','.join('%s' % i for i in caseValue)

            suite.suite_name = suite_name
            suite.describe = describe
            # suite.projectId = projectId
            suite.caseIds = caseIds
        db.session.commit()
        return restful.success()

    def get(self):  # get
        projectId = request.args.get('projectId')
        result = {
            "suites": []
        }
        if projectId is not None:
            suites = UiSuite.query.filter(and_(UiSuite.projectId == projectId)).all()
        else:
            suites = UiSuite.query.all()

        for suite in suites:
            suite_name = suite.suite_name
            create_time = suite.create_time
            describe = suite.describe
            project = AlterProject.query.filter(AlterProject.id == suite.projectId).first()

            result["suites"].append({
                "序号": suite.id,
                "套件名称": suite_name,
                "所属项目": project.projectName,
                "描述信息": describe,
                "创建时间": create_time.strftime("%Y-%m-%d %H:%M:%S"),
                "suiteId": suite.id,
                "suiteName": suite_name,
                "projectName": project.projectName,
                "describe": describe
            })

        result["suiteCols"] = suiteCols
        return restful.success(data=result)


api.add_resource(UiSuiteOperation, '/uiSuiteOperation')


@ui_suite.route("/runSuite", methods=['POST'])
def run_suite():
    ip = get_user_ip(request)
    data = request.get_data()
    json_data = json.loads(data.decode("utf-8"))
    suiteId = json_data["suiteId"]
    userId = json_data["userId"]
    isAgain = json_data["isAgain"]
    deviceId = json_data["deviceId"]  # 设备名

    caseIdCode = "UI" + str((int(round(time.time() * 1000))))
    source = 0
    success_num = 0
    error_num = 0
    deviceObj = UiDevices.query.filter(UiDevices.id == deviceId).first()  # 获取启动的设备
    # 启动服务
    # if int(deviceObj.status) == 0:
    # 机器未启动
    if int(deviceObj.is_run) == 1:
        return restful.server_error("设备正在运行")

    if not start_appium(**{"deviceObj": deviceObj, "ip": ip, "isAgain": isAgain}):
        return restful.server_error()

    deviceObj.is_run = 1
    db.session.commit()

    time.sleep(5)
    suite = UiSuite.query.filter(UiSuite.id == suiteId).first()
    caseIds = str(suite.caseIds).split(",")
    projectId = suite.projectId
    try:
        db.session.add(
            AlterExecuteLog(caseId=caseIdCode, source=source, success_num=success_num, error_num=error_num,
                            amount=len(caseIds), log_type=1,projectId=projectId,time=10))
        db.session.commit()
    except Exception as e:
        print(repr(e))
        print("插入AlterExecuteLog： 失败")

    for caseId in caseIds:
        caseObj = UiCase.query.filter(UiCase.id == caseId).first()
        print("执行用例: ", caseId)
        steps = UiStep.query.order_by(db.desc(UiStep.sort)).filter(
            and_(UiStep.caseId == caseId, UiStep.is_delete == 0)).all()  # 获取 步骤
        print("执行用例内容: ", steps)
        for step in steps:
            operation = step.operation
            element_name = None
            element_type = None
            element_path = None

            if step.elementId is not None:
                # elementId 有可能是空
                element = UiElements.query.filter(UiElements.id == step.elementId).first()
                element_name = element.element_name
                element_type = element.element_type
                element_path = element.element_path

            activity_name = None
            activity_path = None
            activityObj = UiActivitys.query.filter(UiActivitys.id == step.activityId).first()
            if activityObj is not None:
                activity_name = activityObj.activity_name
                activity_path = activityObj.activity_path

            caseTitle = operation
            if operation != "左滑" and operation != "右滑" and operation != "上滑" and operation != "下滑" and operation != "返回":
                caseTitle += ("--" + activity_name)

                if operation != "断言跳转" and operation != "切换界面":
                    caseTitle += (":" + ("" if element_name is None else element_name))

                if operation == "输入":
                    caseTitle += (":" + "(" + step.content + ")")

            kwargs = {
                "element": {
                    "element_name": element_name,
                    "element_type": element_type,
                    "element_path": element_path,
                    "content": step.content
                },
                "operation": operation,
                "ip": ip,
                "activityObj": {
                    "activityId": step.activityId,
                    "activityName": activity_name,
                    "activityPath": activity_path
                },
                "elementId": step.elementId,
                "caseName": caseObj.case_name,
                "caseTitle": caseTitle,
                "caseId": caseIdCode,
                "deviceObj": {
                    "device_port": deviceObj.device_port,
                    "device_bp": deviceObj.device_bp,
                    "deviceName": deviceObj.device
                }
            }

            execute_step(**kwargs)

    quit_device(deviceObj, ip, 0)
    deviceObj.is_run = 0
    db.session.commit()
    return restful.success(message="执行完毕...")


@ui_suite.route("/quitServer", methods=["POST"])
def quit_server():
    """关闭服务"""
    ip = get_user_ip(request)
    data = request.get_data()
    json_data = json.loads(data.decode("utf-8"))
    deviceId = json_data["deviceId"]
    quitType = json_data["quitType"]

    deviceObj = UiDevices.query.filter(UiDevices.id == deviceId).first()  # 获取启动的设备
    quit_device(deviceObj, ip, quitType)
    return restful.success()


def quit_device(deviceObj, ip, quitType):
    """
    退出集合，
    :return:
    """
    requests.post(url="http://{ip}:6060/appium/quitServer".format(ip=ip), json={
        "deviceName": deviceObj.device,
        "ip": ip,
        "quitType": quitType
    })
    deviceObj.status = 0



@ui_suite.route("/getStartupConfig")
def get_startup_config():
    """
    获取启动配置
    :return:
    """
    ip = get_user_ip(request)
    # 获取可用设备
    devices = UiDevices.query.all()
    devices_usable = []
    try:
        devices_usable = get_connect_devices(ip)
    except Exception as e:
        print(repr(e))

    result = {
        "devices": []
    }
    for device in devices:
        if device.device in devices_usable:
            result["devices"].append({
                "device": device.device,
                "describe": device.describe,
                "id": device.id
            })

    return restful.success(data=result)


def get_connect_devices(ip):
    devices = requests.get(url="http://{ip}:6060/appium/getConnectDevices".format(ip=ip)).json()["obj"]
    # for device in devices:
    #     deviceObj = UiDevices.query.filter(UiDevices.device == device).first()
    #     if deviceObj is None:
    #         db.session.add(UiDevices(device=device, ip="127.0.0.1", userId=0))
    #
    # db.session.commit()
    return devices


@ui_suite.route("/getRunLog")
def run_log():
    caseId = request.args.get('caseId')
    execute = AlterExecuteLog.query.filter(AlterExecuteLog.caseId == caseId).first()

    run_results = mongo.db.uiRunLog.find({"caseId": caseId})
    data = json.loads(json_util.dumps(run_results))
    print(type(data))
    if execute is None:
        return restful.success(data=data)
    else:
        return restful.success(data={
            "runResults": data,
            "executeResult": {
                "successNum": execute.success_num,
                "errorNum": execute.error_num,
                "amountNum": execute.amount,
                "skipNum": 0
            }
        })
