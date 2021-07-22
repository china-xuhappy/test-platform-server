"""
和数据库 映射类
"""
from exts import db
from datetime import datetime
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship


class AlterInterface(db.Model):
    __tablename__ = "alter_interface"
    id = db.Column(db.Integer(), unique=False, primary_key=True, autoincrement=True)
    method = db.Column(db.String(255))
    type = db.Column(db.String(255))  # http, https
    host = db.Column(db.String(255))
    route = db.Column(db.String(255))
    url = db.Column(db.String(255))
    projectId = db.Column(db.Integer(), ForeignKey('alter_project.id'))
    isFormData = db.Column(db.String(255))
    name = db.Column(db.String(255))
    is_delete = db.Column(db.String(2))  # 1删除 0未删除

    param = relationship('AlterParams', back_populates='interface')

    def __init__(self, url, type, host, route, method, projectId, name):
        self.url = url
        self.type = type
        self.host = host
        self.route = route
        self.method = method
        self.projectId = projectId
        self.name = name
        self.is_delete = 0


# 参数和接口和项目关联在一起的
class AlterParams(db.Model):
    __tablename__ = "alter_params"

    id = db.Column(db.Integer(), unique=False, primary_key=True, autoincrement=True)
    catalogueId = db.Column(db.Integer(), ForeignKey('alter_catalogue.id'))
    interfaceId = db.Column(db.Integer(), ForeignKey('alter_interface.id'))
    describe = db.Column(db.String(255))
    params = db.Column(db.String(6000))
    headers = db.Column(db.String(3000))
    method = db.Column(db.String(255))
    isFormData = db.Column(db.String(255))
    # beforeSqls = db.Column(db.String(1000))
    # assertSqls = db.Column(db.String(1000))
    # initialTests = db.Column(db.String(3000))
    templateIds = db.Column(db.String(255))
    rests = db.Column(db.String(255))
    is_delete = db.Column(db.Integer())  # 1删除 0未删除
    sqls = db.Column(db.String(3000))
    flag = db.Column(db.Integer())  # 1删除 0未删除

    catalogue = relationship('AlterCatalogue', back_populates="params")
    interface = relationship("AlterInterface", back_populates='param')
    flow = relationship('AlterFlow', back_populates="params")
    # runLog = relationship('AlterRunLog', back_populates="paramsObj")

    __mapper_args__ = {
        "order_by": flag.desc()
    }

    # runLog = relationship('AlterRunLog', back_populates='runLog')

    def __init__(self, catalogueId, interfaceId, params, headers, describe, method, flag):
        self.catalogueId = catalogueId
        self.interfaceId = interfaceId
        self.params = params
        self.headers = headers
        self.describe = describe
        self.method = method
        self.isFormData = "False"
        self.rests = "{\"variableName\":\"\",\"isVariable\":\"false\",\"waitVlue\": 0, \"isWaitVariable\": \"false\"}"
        self.is_delete = 0
        self.sqls = "[\"\"]"
        self.flag = flag


alter_user_project = db.Table(
    'alter_user_project',
    db.Column('user_id', db.Integer, db.ForeignKey('alter_user.id'), primary_key=True),
    db.Column('project_id', db.Integer, db.ForeignKey('alter_project.id'), primary_key=True)
)


class AlterProject(db.Model):
    __tablename__ = "alter_project"
    id = db.Column(db.Integer(), unique=False, primary_key=True, autoincrement=True)
    projectName = db.Column(db.String(255))
    # isPrivate = db.Column(db.String(2))
    is_delete = db.Column(db.String(2))  # 1删除 0未删除
    project_type = db.Column(db.String(2))  # 0 接口项目， 1 UI自动化项目

    users = relationship("AlterUser", secondary=alter_user_project, back_populates="projects")
    catalogues = relationship('AlterCatalogue', back_populates="projects")
    gathers = relationship('AlterCaseGather', back_populates="projects")
    python_files = relationship('AlterFiles', back_populates="projects")

    def __init__(self, projectName):
        self.projectName = projectName
        self.is_delete = 0
        self.project_type = 0


class AlterFiles(db.Model):
    """
    项目下面用到的python代码文件
    """
    __tablename__ = "alter_files"
    id = db.Column(db.Integer(), unique=False, primary_key=True, autoincrement=True)
    project_id = db.Column(db.Integer(), ForeignKey('alter_project.id'))
    file_name = db.Column(db.String(255))
    is_delete = db.Column(db.String(2))  # 1删除 0未删除


    projects = relationship("AlterProject", order_by=AlterProject.id, back_populates="python_files")

    def __init__(self, project_id, file_name):
        self.project_id = project_id
        self.file_name = file_name
        self.is_delete = 0

class AlterCaseGather(db.Model):
    """
    接口用例集
    """
    __tablename__ = "alter_case_gather"
    id = db.Column(db.Integer(), unique=False, primary_key=True, autoincrement=True)
    gatherName = db.Column(db.String(255))
    projectId = db.Column(db.Integer(), ForeignKey('alter_project.id'))

    projects = relationship("AlterProject", order_by=AlterProject.id, back_populates="gathers")
    flows = relationship('AlterFlow', back_populates="gathers")

    def __init__(self, gatherName, projectId):
        self.gatherName = gatherName
        self.projectId = projectId


class AlterCatalogue(db.Model):
    __tablename__ = "alter_catalogue"
    id = db.Column(db.Integer(), unique=False, primary_key=True, autoincrement=True)
    catalogueName = db.Column(db.String(255))
    projectId = db.Column(db.Integer(), ForeignKey('alter_project.id'))
    is_delete = db.Column(db.Integer())
    catalogueId = db.Column(db.Integer())

    params = relationship("AlterParams", order_by=AlterParams.flag.desc(), back_populates="catalogue")
    projects = relationship("AlterProject", order_by=AlterProject.id, back_populates="catalogues")

    def __init__(self, catalogueName, projectId, catalogueId):
        self.catalogueName = catalogueName
        self.projectId = projectId
        self.is_delete = 0
        self.catalogueId = catalogueId


# class AlterUser(db.Model):
#     __tablename__ = "alter_user"
#     id = db.Column(db.Integer(), unique=False, primary_key=True, autoincrement=True)
#     userName = db.Column(db.String(255))
#     userPassword = db.Column(db.String(255))
#
#
#     def __init__(self, userName, userPassword):
#         self.userName = userName
#         self.userPassword = userPassword

from werkzeug.security import generate_password_hash, check_password_hash


class AlterUser(db.Model):
    __tablename__ = "alter_user"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(255))
    _password = db.Column(db.String(255))
    useDatas = db.Column(db.String(3000))
    ip = db.Column(db.String(255))

    projects = relationship("AlterProject", secondary=alter_user_project, back_populates="users")

    def __init__(self, username, password, ip):
        self.username = username
        self.password = password
        self.ip = ip
        self.useDatas = "[{\"variableName\": "",\"variableValue\": [""],\"typeOptions\":\"String\"}]"

    @property
    def password(self):
        return self._password

    @password.setter
    def password(self, raw_password):
        self._password = generate_password_hash(raw_password)

    def check_password(self, raw_password):
        result = check_password_hash(self.password, raw_password)
        return result


class AlterEnvironment(db.Model):
    __tablename__ = "alter_environment"
    id = db.Column(db.Integer(), unique=False, primary_key=True, autoincrement=True)
    environmentName = db.Column(db.String(255))

    def __init__(self, environmentName):
        self.environmentName = environmentName


class AlterHost(db.Model):
    __tablename__ = "alter_host"
    id = db.Column(db.Integer(), unique=False, primary_key=True, autoincrement=True)
    environmentId = db.Column(db.Integer(), ForeignKey('alter_environment.id'))
    name = db.Column(db.String(255))
    host = db.Column(db.String(255))
    is_delete = db.Column(db.String(2))

    def __init__(self, environmentId, name, host):
        self.environmentId = environmentId
        self.name = name
        self.host = host
        self.is_delete = 0


# class AlterSonNavigation(db.Model):
#     __tablename__ = "alter_son_navigation"
#     id = db.Column(db.Integer(), unique=False, primary_key=True, autoincrement=True)
#     navigationId = db.Column(db.Integer(), ForeignKey('alter_navigation.id'))
#     sonName = db.Column(db.String(255))
#
#     sonNavigation = relationship('AlterNavigation', back_populates="sonNavigations")
#     # son_flow = relationship('AlterFlow', back_populates="son_navigation")
#
#     def __init__(self, navigationId, sonName):
#         self.navigationId = navigationId
#         self.sonName = sonName

# class AlterNavigation(db.Model):
#     __tablename__ = "alter_navigation"
#     id = db.Column(db.Integer(), unique=False, primary_key=True, autoincrement=True)
#     navigationName = db.Column(db.String(255))
#
#     sonNavigations = relationship("AlterSonNavigation",order_by=AlterSonNavigation.id, back_populates="sonNavigation")
#
#     def __init__(self, navigationName):
#         self.navigationName = navigationName

class AlterFlow(db.Model):
    __tablename__ = "alter_flow"
    id = db.Column(db.Integer(), unique=False, primary_key=True, autoincrement=True)
    gatherId = db.Column(db.Integer(), ForeignKey('alter_case_gather.id'))
    name = db.Column(db.String(255))  # 用例名，描述。。
    paramsId = db.Column(db.Integer(), ForeignKey('alter_params.id'))
    rests = db.Column(db.String(255))  # 其他配置
    sort = db.Column(db.Integer())
    parameters = db.Column(db.String(3000))  # 接口报文参数
    update_time = db.Column(db.DateTime)  # 修改时间

    is_delete = db.Column(db.String(2))

    params = relationship("AlterParams", order_by=AlterParams.id, back_populates="flow")
    gathers = relationship("AlterCaseGather", order_by=AlterCaseGather.id, back_populates="flows")

    def __init__(self, gatherId, name, paramsId, rests, sort):
        self.gatherId = gatherId
        self.name = name
        self.paramsId = paramsId
        self.rests = rests
        self.is_delete = 0
        self.sort = sort
        self.update_time = datetime.now()
        self.parameters = "[{'variableName': '','variableValue': '' ,'typeOptions':'String'}]".replace("\'", '\"')


"""
接口参数模板表，
暂时未细开发
"""


class AlterTemplate(db.Model):
    __tablename__ = "alter_template"
    id = db.Column(db.Integer(), unique=False, primary_key=True, autoincrement=True)
    templateParams = db.Column(db.String(5000))

    def __init__(self, templateParams):
        self.templateParams = templateParams


"""
用例执行日志
"""


class AlterExecuteLog(db.Model):
    __tablename__ = "alter_execute_log"
    id = db.Column(db.Integer(), unique=False, primary_key=True, autoincrement=True)
    caseId = db.Column(db.String(255))  # 执行caseId 和 alter_run_log 有关联
    create_time = db.Column(db.DateTime)  # 创建时间
    source = db.Column(db.String(2))  # 来源 0 手动执行， 1 定时任务
    success_num = db.Column(db.Integer())  # 成功用例数量
    error_num = db.Column(db.Integer())  # 失败用例数量
    amount = db.Column(db.Integer())  # 用例总数
    is_read = db.Column(db.Integer())  # 0未阅读，1已阅读
    log_type = db.Column(db.String(2))  # 0接口自动化，1UI自动化
    time = db.Column(db.String(255))  # 耗时秒级别
    projectId = db.Column(db.Integer())
    gatherId = db.Column(db.String(255))  # 存储分组ID，便于log查询

    __mapper_args__ = {
        "order_by": create_time.desc()
    }

    def __init__(self, caseId, source, success_num, error_num, amount, log_type, projectId, time=0, gatherId=""):
        self.caseId = caseId
        self.source = source
        self.success_num = success_num
        self.error_num = error_num
        self.amount = amount
        self.create_time = datetime.now()
        self.is_read = 0
        self.log_type = log_type
        self.time = time
        self.projectId = projectId
        self.gatherId = gatherId


# class ApschedulerJobs(db.Model):
#     __tablename__ = "apscheduler_jobs"
#
#     id = db.Column(db.String(191), unique=False, primary_key=True)
#     next_run_time = db.Column(db.Float)
#     job_state = db.Column(db.BLOB)
#
#     def __init__(self, id, next_run_time, job_state):
#         self.id = id
#         self.next_run_time = next_run_time
#         self.job_state = job_state


# 定时任务
class AlterTasks(db.Model):
    __tablename__ = "alter_tasks"

    id = db.Column(db.Integer(), unique=False, primary_key=True, autoincrement=True)
    jobId = db.Column(db.String(255))
    task_name = db.Column("task_name", db.String(255))
    task_cron = db.Column(db.String(255))
    task_status = db.Column(db.String(2))  # 0正常启动，1暂停
    projectId = db.Column(db.Integer(), ForeignKey('alter_project.id'))
    task_args = db.Column(db.String(255))
    task_type = db.Column(db.String(2))  # 0接口定时任务, 1测试集定时任务, 2项目定时任务,
    userId = db.Column(db.Integer(), ForeignKey('alter_user.id'))
    create_time = db.Column(db.DateTime)
    is_delete = db.Column(db.String(2))  # 1删除 0未删除

    projects = relationship("AlterProject", order_by=AlterProject.id)

    def __init__(self, jobId, task_name, task_cron, projectId, task_args, task_type, userId):
        self.jobId = jobId
        self.task_name = task_name
        self.task_cron = task_cron
        self.task_status = 0
        self.projectId = projectId
        self.task_args = task_args
        self.task_type = task_type
        self.userId = userId
        self.create_time = datetime.now()
        self.is_delete = 0
