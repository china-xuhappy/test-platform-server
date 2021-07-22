"""
和数据库 映射类
"""
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship

from controller.project.models import AlterProject
from exts import db
from datetime import datetime


class UiCase(db.Model):
    """
    测试用例
    """
    __tablename__ = "ui_case"
    id = db.Column(db.Integer(), unique=False, primary_key=True, autoincrement=True)
    case_name = db.Column(db.String(255))  # 用例名
    describe = db.Column(db.String(1000))  # 用例描述

    projectId = db.Column(db.Integer(), ForeignKey('alter_project.id'))
    create_time = db.Column(db.DateTime)  # 创建时间

    is_delete = db.Column(db.Integer())  # 是否删除 0 未删除 1删除
    projects = relationship("AlterProject", order_by=AlterProject.id)

    def __init__(self, case_name, describe, projectId):
        self.case_name = case_name
        self.describe = describe
        self.projectId = projectId
        self.create_time = datetime.now()
        self.is_delete = 0


class UiStep(db.Model):
    """
    用例步骤
    """
    __tablename__ = "ui_steps"
    id = db.Column(db.Integer(), unique=False, primary_key=True, autoincrement=True)
    operation = db.Column(db.String(255))  # 操作：输入，点击，滑动，等操作
    caseId = db.Column(db.Integer(), ForeignKey('ui_case.id'))  # 用例Id
    elementId = db.Column(db.Integer(), ForeignKey('ui_elements.id'))  # 元素Id
    activityId = db.Column(db.Integer(), ForeignKey('ui_activitys.id')) # 页面Id

    content = db.Column(db.String(255))  # 内容
    sort = db.Column(db.Integer())  # 排序
    is_delete = db.Column(db.Integer())  # 是否删除 0 未删除 1删除
    create_time = db.Column(db.DateTime)  # 创建时间
    update_time = db.Column(db.DateTime)  # 更新时间

    def __init__(self, operation, caseId, elementId, activityId , content, sort):
        self.operation = operation
        self.caseId = caseId
        self.elementId = elementId
        self.activityId = activityId
        self.content = content
        self.is_delete = 0
        self.create_time = datetime.now()
        self.sort = sort
