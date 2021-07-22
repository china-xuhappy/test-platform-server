"""
选择不同环境时的配置工具类
"""
from exts import db_test2, db_test1, db_test5, fat_1, fat_2, fat_3, redis_test1,redis_test2,redis_test3,redis_test4,redis_test5,redis_fat1,redis_fat2,redis_fat3

def get_redis_object(enviroment):
    """
    根据不同环境返回redis
    :param enviroment: 环境 1，2，3，4，5
    :return:
    """
    if enviroment == "1":
        return redis_test1
    elif enviroment == "2":
        return redis_test2
    elif enviroment == "3":
        return redis_test3
    elif enviroment == "4":
        return redis_test4
    elif enviroment == "5":
        return redis_test5
    elif enviroment == "6":
        return redis_fat1
    elif enviroment == "7":
        return redis_fat2
    elif enviroment == "8":
        return redis_fat3
    else:
        return "暂时无此环境"

def gat_db_object(interceptor):
    """
    通过环境 获取数据库对象
    :param interceptor:
    :return:
    """
    db_test = fat_1
    # 创建数据库的表
    if interceptor == "1":
        db_test = db_test1
    elif interceptor == "2":
        db_test = db_test2
    elif interceptor == "5":
        db_test = db_test5
    elif interceptor == "6":
        db_test = fat_1
    elif interceptor == "7":
        db_test = fat_2
    elif interceptor == "8":
        db_test = fat_3
    return db_test

