from concurrent.futures.thread import ThreadPoolExecutor

import pymysql
from flask_sqlalchemy import SQLAlchemy
from flask_apscheduler import APScheduler

from utils.email_utils import SendMail
from utils.mysql_utils import DBHelper
from redis import Redis
from flask_pymongo import PyMongo

scheduler = APScheduler()
db = SQLAlchemy(session_options={"autoflush": False})
# redis配置
redis_test1 = Redis(host="10.0.3.200",port=6379)
redis_test2 = Redis(host="10.0.3.211", port=6379)
redis_test3 = Redis(host="10.0.3.206", port=6379)
redis_test4 = Redis(host="10.0.3.224", port=6379)
redis_test5 = Redis(host="121.199.4.107", port=6379)
redis_fat1 = Redis(host="172.16.22.212", port=6379)
redis_fat2 = Redis(host="172.16.22.217", port=6379)
redis_fat3 = Redis(host="172.16.22.222", port=6379)

mail = SendMail()
mongo = PyMongo()

executor = ThreadPoolExecutor(max_workers=10)

db_test1,db_test2,db_test3,db_test4,db_test5,fat_1,fat_2,fat_3 = None,None,None,None,None,None,None,None

console_db_test1,console_db_test2,console_db_test3,console_db_test4,console_db_test5 = None,None,None,None,None
db_xs = None
db_secondary = None
atzuchedb = None
#线上的

# db_xs,atzuchedb,db_secondary = None,None,None

# import gitlab
# gitlab_client = gitlab.Gitlab(url="http://123.56.28.90:9981", http_username="root", http_password="xukaixin", timeout=2)
gitlab_client = None