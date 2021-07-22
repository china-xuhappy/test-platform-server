"""
和appium服务的工具类
"""
import datetime
import requests
from exts import db, mongo


def get_user_ip(request):
    if request.headers.get('X-Forwarded-For'):
        return request.headers['X-Forwarded-For']
    elif request.headers.get('X-Real-IP'):
        return request.headers.get('X-Real-IP')
    else:
        return request.remote_addr


def start_appium(**kwargs):

    caseId = None
    isAgain = 0
    if "caseId" in kwargs:
        caseId = kwargs["caseId"]
    if "isAgain" in kwargs:
        isAgain = kwargs["isAgain"]

    deviceObj = kwargs["deviceObj"]
    deviceObj.status = 1
    db.session.commit()

    ip = kwargs["ip"]

    try:
        relust = requests.post(url="http://{ip}:6060/appium/startAppium".format(ip=ip), json={
            "caseId": caseId,
            "deviceName": deviceObj.device,
            "appium_ip": ip,
            "appium_port": deviceObj.device_port
        }).json()
        if relust["status"] != 200:
            return False
    except Exception as e:
        print(repr(e))
        return False

    try:
        relust = requests.post(url="http://{ip}:6060/appium/connectAppium".format(ip=ip), json={
            "appiumArgs": {
                "platformName": "Android",
                "platformVersion": "7.1.2",
                "deviceName": deviceObj.device,
                "appPackage": "com.Autoyol.auto",
                "appActivity": "com.Autoyol.main_v60.SplashActivity"
            },
            "deviceName": deviceObj.device,
            "isAgain": isAgain
        }).json()
        if relust["status"] != 200:
            return False
    except Exception as e:
        print(repr(e))
        return False

    return True


def execute_step(**kwargs):
    """
    封装 用来执行用例的
    appium服务返回500 说明服务没启动 或者 中途报错了。 要到上层去处理，这层方法不做回退 或者 重置什么操作
    :param kwargs:
    :return:
    """
    activityId = None
    if "activityObj" in kwargs:
        activityId = kwargs["activityObj"]["activityId"]
    operation = kwargs["operation"]
    deviceName = kwargs["deviceObj"]["deviceName"]
    ip = kwargs["ip"]

    result = requests.post(url="http://{ip}:6060/appium/executeStep".format(ip=ip), json=kwargs).json()
    print(result)
    errImage = ""
    errorLog,errContent = "",""
    status = 0
    if result["status"] != 500:  # 执行成功
        resultObj = result["obj"]
        if not resultObj["status"]:  # 用例执行失败 ,False 但是第二个不宜久有值
            errorLog = resultObj["errorContent"]
            errImage = errorLog["image_url"]
            errContent = errorLog["content"]
            status = 1

    mongo.db.uiRunLog.insert_one(
        {
            "activityId": activityId,
            "ip": ip,
            "device": deviceName,
            "operation": operation,
            "elementId": kwargs["elementId"],
            "caseId": kwargs["caseId"],
            "caseName": kwargs["caseName"],
            "caseTitle": kwargs["caseTitle"],
            "caseTime": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "status": status,
            "elementObj": kwargs["element"],
            "activityObj": kwargs["activityObj"],
            "errImage": errImage,
            "errContent": errContent,
            # "results": results,  # 返回结果，成功是失败， 给前端的
            "errorLog": errorLog,  # 错误日志，有可能是报错图片，有可能是执行的报错
            "operationLog": kwargs,  # 请求的操作日志
            "resultLog": result,  # 请求的返回结果日志
        }
    )
    return result, status
