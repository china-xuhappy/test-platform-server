import datetime


def timeDayChange(day: int, hour: int) -> str:
    """
    获取某天某个小时时间 格式: 20200915020000
    :param day:
    :param hour:
    :return:
    """

    now_time = datetime.datetime.now()
    change_time = now_time + datetime.timedelta(days=day)
    now_time = change_time - datetime.timedelta(minutes=change_time.minute, seconds=change_time.second)
    now_time = now_time.replace(hour=hour)
    return now_time.strftime("%Y%m%d%H%M%S")


def getToDayTime() -> str:
    """
    获取当天时间 格式: 20200914
    :param day:
    :param hour:
    :return:
    """

    now_time = datetime.datetime.now()
    return now_time.strftime("%Y%m%d")


def timeHourChange(hour: int, minute: int) -> str:
    """
    获取当前时间 加几小时， 设置几分钟： 格式：20200914145900
    :param minute:
    :param hour:
    :return:
    """

    now_time = datetime.datetime.now()
    now_time = now_time + datetime.timedelta(hours=hour)
    now_time = now_time.replace(minute=minute, second=0)
    return now_time.strftime("%Y%m%d%H%M%S")


def timeChange1412(day: int, hour: int) -> str:
    """
    获取某天某个小时时间 格式: 2020-09-15 02:00:00
    :param day:
    :param hour:
    :return:
    """

    now_time = datetime.datetime.now()
    change_time = now_time + datetime.timedelta(days=day)
    now_time = change_time - datetime.timedelta(minutes=change_time.minute, seconds=change_time.second)
    now_time = now_time.replace(hour=hour)
    return now_time.strftime("%Y-%m-%d %H:%M:%S")
