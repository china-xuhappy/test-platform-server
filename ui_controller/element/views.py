"""
用户相关接口
"""
from flask import Blueprint, jsonify, g, render_template, request
from flask_restful import Api, Resource, marshal_with, reqparse, fields
from sqlalchemy import and_

from ui_controller.element.models import UiActivitys, UiElements
from utils.appium_tool import get_user_ip

element = Blueprint('element', __name__, url_prefix='/element')
from exts import db

api = Api(element)
from utils import restful
from controller.project.models import AlterUser
import json, config, os
from utils.ui_utils import ui_img_utils
from utils.ui_utils import ui_xml_parse
import xml.dom.minidom

activityCols = [
    {
        "label": "序号"
    },
    {
        "label": "描述信息"
    },
    {
        "label": "页面名称"
    },
]


class ActivityManage(Resource):
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('activityName', required=False, type=str)  # 页面名
        parser.add_argument('activityPath', required=False, type=str)  # 页面地址
        parser.add_argument('projectId', required=False, type=int)  # 项目ID
        parser.add_argument('describe', required=False, type=str)  # 项目描述
        parser.add_argument('activityId', required=False, type=int)  # activityId
        parser.add_argument('typeStatus', required=True, type=int)  # 0新增，1修改，2删除
        args = parser.parse_args()
        type_status = args["typeStatus"]

        activity_name = args["activityName"]
        activity_path = args["activityPath"]
        projectId = args["projectId"]
        describe = args["describe"]

        if type_status == 0:
            activity = UiActivitys(activity_name=activity_name, activity_path=args["activityPath"],
                                   projectId=args["projectId"], describe=args["describe"])
            db.session.add(activity)

        elif type_status == 1:
            activity = UiActivitys.query.filter(UiActivitys.id == args["activityId"]).first()
            activity.activity_name = activity_name
            activity.activity_path = activity_path
            activity.projectId = projectId
            activity.describe = describe

        elif type_status == 2:
            activity = UiActivitys.query.filter(UiActivitys.id == args["activityId"]).first()
            activity.is_delete = 1

        db.session.commit()
        return restful.success("成功")

    resource_fields = {
        "id": fields.Integer,
        "activity_name": fields.String,
        "img_url": fields.String
    }

    @marshal_with(resource_fields)
    def get(self):  # get
        projectId = request.args.get('projectId')
        return UiActivitys.query.filter(and_(UiActivitys.projectId == projectId, UiActivitys.is_delete == 0)).all()


api.add_resource(ActivityManage, '/activityManage')


@element.route("/getActivitys")
def get_activitys():
    """
    获取所有界面
    :return:
    """
    ip = get_user_ip(request)
    projectId = request.args.get('projectId')
    activityList = []
    activitys = UiActivitys.query.filter(and_(UiActivitys.projectId == projectId, UiActivitys.is_delete == 0)).all()
    for activity in activitys:
        activityList.append({
            "序号": activity.id,
            "页面名称": activity.activity_name,
            "页面地址": activity.activity_path,
            "创建时间": activity.create_time.strftime("%Y-%m-%d %H:%M:%S"),
            "描述信息": activity.describe,
            "id": activity.id,
            "activityName": activity.activity_name,
            "activityPath": activity.activity_path,
            "describe": activity.describe
        })

    return restful.success(data={
        "activitys": activityList,
        "activityCols": activityCols
    })


@element.route("/deleteElement", methods=['POST'])
def delete_element():
    """
    删除步骤
    :return:
    """
    ip = get_user_ip(request)
    data = request.get_data()
    json_data = json.loads(data.decode("utf-8"))
    elementId = json_data["elementId"]  # 步骤ID
    element = UiElements.query.filter(UiElements.id == elementId).first()
    element.is_delete = 1
    db.session.commit()

    return restful.success()


class ElementsOperation(Resource):
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('elementDatas', required=True, type=list)  # 元素数组
        parser.add_argument('activityId', required=True, type=int)  # 页面Id

        args = parser.parse_args()
        elementDatas = args["elementDatas"]
        for elementData in elementDatas:
            if elementData["element_name"] == "" or elementData["element_path"] == "":
                return restful.params_error(message="请填写元素名，元素地址")

            if "id" in elementData:
                id = elementData["id"]
                ui = UiElements.query.filter(UiElements.id == id).first()
                ui.element_name = elementData["element_name"]
                ui.element_type = elementData["element_type"]
                ui.element_path = elementData["element_path"]
            else:
                element = UiElements.query.filter(and_(UiElements.activityId == args["activityId"],
                                                       UiElements.element_name == elementData["element_name"])).first()
                if element is not None:
                    print(elementData["element_name"])
                    return restful.params_error(message="元素名有重复...")

                db.session.add(
                    UiElements(element_name=elementData["element_name"], element_type=elementData["element_type"],
                               element_path=elementData["element_path"], activityId=args["activityId"]))

        db.session.commit()
        return restful.success(message="保存成功..")

    resource_fields = {
        "id": fields.Integer,
        "element_name": fields.String,
        "element_type": fields.String,
        "element_path": fields.String,
    }

    @marshal_with(resource_fields)
    def get(self):  # get
        activityId = request.args.get('activityId')
        return UiElements.query.filter(and_(UiElements.activityId == activityId, UiElements.is_delete == 0)).all()


api.add_resource(ElementsOperation, '/elementsOperation')


@element.route("/acquireActivitySign")
def acquire_activity_sign():
    """
    获取页面的标记位置 -- 主要用于查看元素是哪个按钮
    :return:
    """
    ip = get_user_ip(request)
    elementId = request.args.get('elementId')
    element = UiElements.query.filter(UiElements.id == elementId).first()
    activity = element.activity
    img_path = config.UI_AUTO_PROJECT_IMG + activity.img_file_path

    # return restful.success(data={
    #     "base64": str(ui_img_utils.cv2_base64(ui_img_utils.cv2_sign(img_path, eval(element.bound_first), eval(element.bound_last))),encoding = "utf-8")
    # })


@element.route("/elementXmlImport", methods=['POST'])
def element_xml_import():
    """
    appium xml 导入
    :return:
    """
    ip = get_user_ip(request)
    file = request.files['file']
    filename = file.filename
    if not filename.endswith(".xml"):
        return restful.params_error("请上传xml文件")

    activityId = request.form['activityId']

    file_path = os.path.join("appium_xml", filename)

    appium_xml_path = os.path.join(config.UPLOAD_UI_APPIUM_XML, file_path)
    file.save(appium_xml_path)

    activity = UiActivitys.query.filter(and_(UiActivitys.id == activityId, UiActivitys.is_delete == 0)).first()
    activity.xml_file_path = file_path
    document_tree = xml.dom.minidom.parse(appium_xml_path)
    ui_xml_parse.elements = []
    elements = ui_xml_parse.parseAppiumXml(document_tree.documentElement)
    print(elements)
    for element in elements:
        db.session.add(
            UiElements(element_name=element["text"], element_type="ID",
                       element_path=element["resource_id"], activityId=activityId,
                       bound_first=element["bound_first"],bound_last=element["bound_last"],clickable=element["clickable"],
                       enabled=element["enabled"],checkable=element["checkable"],text_=element["text"])
        )
    db.session.commit()
    return restful.success("成功")