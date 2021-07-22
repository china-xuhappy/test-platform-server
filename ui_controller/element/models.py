"""
和数据库 映射类
"""
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship

from controller.project.models import AlterProject
from exts import db
from datetime import datetime


class UiActivitys(db.Model):
    __tablename__ = "ui_activitys"
    id = db.Column(db.Integer(), unique=False, primary_key=True, autoincrement=True)
    activity_name = db.Column(db.String(255))  # 页面中文名
    activity_path = db.Column(db.String(255))  # Android 配置的activity地址
    img_url = db.Column(db.String(255))  # activity 图片 -- 方便观看
    img_file_path = db.Column(db.String(255))  # activity 图片 -- 方便观看
    xml_file_path = db.Column(db.String(255))  # xml导入的文件地址
    projectId = db.Column(db.Integer(), ForeignKey('alter_project.id'))
    create_time = db.Column(db.DateTime)  # 创建时间
    describe = db.Column(db.String(255))  # 设备描述
    is_delete = db.Column(db.String(2))  # 1删除 0未删除

    def __init__(self, activity_name, activity_path, projectId,describe):
        self.activity_name = activity_name
        self.activity_path = activity_path
        self.projectId = projectId
        self.create_time = datetime.now()
        self.describe = describe
        self.is_delete = 0


class UiElements(db.Model):
    __tablename__ = "ui_elements"
    id = db.Column(db.Integer(), unique=False, primary_key=True, autoincrement=True)
    element_name = db.Column(db.String(255))  # 页面中文名
    element_type = db.Column(db.String(255))  # 元素类型定位 ID，xpath
    element_path = db.Column(db.String(255)) # Android 配置的元素地址
    bound_first = db.Column(db.String(255)) #前面的坐标定位
    bound_last = db.Column(db.String(255)) #后面的坐标定位
    clickable = db.Column(db.String(1))  # 1:可点击 , 0: 不可点击
    enabled = db.Column(db.String(1))  # 1:有效, 0:无效
    checkable = db.Column(db.String(255))  # 1:可用, 0:不可用
    text_ = db.Column(db.String(255))  # 获取元素的文本

    is_delete = db.Column(db.String(2))  # 1删除 0未删除

    activityId = db.Column(db.Integer(), ForeignKey('ui_activitys.id'))
    activity = relationship("UiActivitys", order_by=UiActivitys.id)

    def __init__(self, element_name, element_type, element_path, activityId, bound_first=0,bound_last=0,clickable=0,enabled=0,checkable=0,text_=""):
        self.element_name = element_name
        self.element_type = element_type
        self.element_path = element_path
        self.activityId = activityId
        self.is_delete = 0
        self.bound_first = bound_first
        self.bound_last = bound_last
        self.clickable = clickable
        self.enabled = enabled
        self.checkable = checkable
        self.text_ = text_

