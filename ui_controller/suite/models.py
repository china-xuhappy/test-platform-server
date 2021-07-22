"""
和数据库 映射类
套件
"""
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship

from controller.project.models import AlterProject
from exts import db
from datetime import datetime


class UiSuite(db.Model):
    """
    测试用例
    """
    __tablename__ = "ui_suite"
    id = db.Column(db.Integer(), unique=False, primary_key=True, autoincrement=True)
    suite_name = db.Column(db.String(255))  # 套件名
    describe = db.Column(db.String(1000))  # 套件描述

    projectId = db.Column(db.Integer(), ForeignKey('alter_project.id'))
    create_time = db.Column(db.DateTime)  # 创建时间
    status = db.Column(db.String(2))  # 0空闲，1运行中
    caseIds = db.Column(db.String(255))  # 存储套件下面的测试Id, 逗号隔开

    projects = relationship("AlterProject", order_by=AlterProject.id)

    def __init__(self, suite_name, describe, projectId):
        self.suite_name = suite_name
        self.describe = describe
        self.projectId = projectId
        self.create_time = datetime.now()
        self.status = 0


class UiDevices(db.Model):
    """
    设备表， 存储设备用的
    """
    __tablename__ = "ui_devices"
    id = db.Column(db.Integer(), unique=False, primary_key=True, autoincrement=True)
    device = db.Column(db.String(255))  # 设备udid
    ip = db.Column(db.String(255))  # 设备ip，绑定到那台机器上
    describe = db.Column(db.String(255))  # 设备描述
    userId = db.Column(db.Integer(), ForeignKey('alter_user.id'))  # userId
    create_time = db.Column(db.DateTime)  # 创建时间

    device_port = db.Column(db.String(255))  # appium port
    device_bp = db.Column(db.String(255))  # appium bp port

    status = db.Column(db.String(2))  # 状态 0未使用，1正在执行
    is_run = db.Column(db.String(2)) # 0未执行，1正在执行用例

    def __init__(self, device, ip, device_port, device_bp,describe):
        self.device = device
        self.ip = ip
        self.describe = None
        self.userId = 1
        self.create_time = datetime.now()
        self.status = 0
        self.device_port = device_port
        self.device_bp = device_bp
        self.describe = describe
        self.is_run = 0

# class UiAppium(db.Model):
#     """
#     appium 管理
#     """
#     __tablename__ = "ui_appium"
#     id = db.Column(db.Integer(), unique=False, primary_key=True, autoincrement=True)
#     appium_port = db.Column(db.String(255))  # appium port
#     appium_bp = db.Column(db.String(255))  # appium bp port
#     appium_args = db.Column(db.String(255))  # appium 执行参数
#     appium_ip = db.Column(db.String(255))  # appium ip
#     create_time = db.Column(db.DateTime)  # 创建时间
#     status = db.Column(db.String(2))  # 执行状态 0未执行，1执行结束
#
#     device_name = db.Column(db.String(255))  # 暂不使用deviceId， 不同项目查SQL不方便。 后期优化
#
#     def __init__(self, appium_port, appium_bp, appium_args, appium_ip, device_name):
#         self.appium_port = appium_port
#         self.appium_bp = appium_bp
#         self.appium_args = appium_args
#         self.appium_ip = appium_ip
#         self.source = 0
#         self.create_time = datetime.now()
#         self.device_name = device_name

