DEBUG = True
import os
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore

USERID = 0

# session
SECRET_KEY = os.urandom(24)

# 数据库
HOSTNAME = None
PORT = '3306'
DATABASE = 'alter'
USERNAME = None
PASSWORD = None
SQLALCHEMY_POOL_RECYCLE = 20
SQLALCHEMY_POOL_SIZE = 100
SQLALCHEMY_TRACK_MODIFICATIONS = True

DEBUG = True
# SQLALCHEMY_ECHO = True

DB_URI = 'mysql+pymysql://{}:{}@{}:{}/{}'.format(USERNAME, PASSWORD, HOSTNAME, PORT, DATABASE)
SQLALCHEMY_DATABASE_URI = DB_URI

SQLALCHEMY_TRACK_MODIFICATIONS = False
# user_id
CMS_USER_ID = "safsdfkjflkjkll"

UPLOAD_FOLDER = '/xuhappy/xmind'

UPLOAD_SECONDARY = '/xuhappy/secondary'
#UPLOAD_SECONDARY = 'E:/secondary'

# UPLOAD_FOLDER = 'E:/'
UPLOAD_FOLDER_YML = '/xuhappy/yml'
# UPLOAD_FOLDER_YML = "E:/"

FUNC_ADDRESS = os.path.abspath('.') + r'/func_list'

UI_CASE_UPLOAD_FOLDER = 'C:/ui_case'

UI_AUTO_PROJECT_IMG = 'C:/ui_auto'

UPLOAD_UI_APPIUM_XML = 'C:/ui_auto'

# UPLOAD_FOLDER = 'E:\\'
# 开关
SCHEDULER_API_ENABLED = True
# 持久化配置
SCHEDULER_JOBSTORES = {
    'default': SQLAlchemyJobStore(url=DB_URI)
}
SCHEDULER_EXECUTORS = {
    'default': {'type': 'threadpool', 'max_workers': 20}
}

MONGO_DBNAME = 'alter'
MONGO_URI = None

secondary_tranStat = None
# 交易类别(tranMemo)
secondary_tran_memo = None
# 交易类别：
