#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @File  : views.py
# @Author: kaixin.xu
# @Date  : 2020/3/17
# @Desc  : 公用接口
from flask import Blueprint, request, g, current_app, make_response, send_from_directory
from flask_restful import Api, Resource, marshal_with, reqparse, fields
from controller.user.models import SecondaryFile
from permission.console_permission import yml_import
from utils.gitlab import gitlab_utils

common = Blueprint('common', __name__, url_prefix='/common')
from utils import restful
from exts import db
import requests, codecs, copy,json,os,config
from utils.aotu_utils.environment_select_util import gat_db_object, get_redis_object

api = Api(common)
from utils.xmind_utils import xmind_utils
from utils.ap_sheduler import APScheduler
from controller.project.models import AlterTasks, AlterEnvironment, AlterExecuteLog, AlterHost, AlterCatalogue, \
    AlterParams
from sqlalchemy import and_
from utils.task_utils import run_task

hostsCols = [
    {
        "label": "name"
    },
    {
        "label": "host"
    }
]


@common.route("/permission/", methods=['POST'])
def permission_import():
    file = request.files['file']
    print(file.filename)
    filename = file.filename
    if not filename.endswith(".yml"):
        return restful.params_error("请上传yml文件")

    yml_url = os.path.join(config.UPLOAD_FOLDER_YML, file.filename)
    file.save(yml_url)

    try:
        for i in range(5):
            yml_import(yml_url, i + 1)
    except Exception as e:
        return restful.server_error("执行失败 !"+ str(e))

    return restful.success(message="导入完毕。。")


@common.route("/xmindToExcle/", methods=['POST'])
def xmind_to_excle():
    file = request.files['file']
    print(file.filename)
    filename = file.filename
    if not filename.endswith(".xmind"):
        return restful.params_error("请上传xmind文件")

    xmind_url = os.path.join(config.UPLOAD_FOLDER, file.filename)
    file.save(xmind_url)

    xmind_utils().write_excel(xmind_url, filename)

    return restful.success()


@common.route('/get_excle/<file_name>', methods=['GET'])
def get_file(file_name):
    file_name = str(file_name)[:str(file_name).index(".")] + ".xls"
    directory = config.UPLOAD_FOLDER
    try:
        response = make_response(
            send_from_directory(directory, file_name, as_attachment=True))
        return response
    except Exception as e:
        print(repr(e))
        return restful.server_error("失败")


class TaskOperation(Resource):
    def get(self):
        projectId = request.args.get('projectId')

        tasks = AlterTasks.query.filter(and_(AlterTasks.projectId == projectId, AlterTasks.is_delete == 0)).all()
        tasks_list = []

        for task in tasks:
            taskStatus = "启动"
            if task.task_status == "1":
                taskStatus = "暂停"

            tasks_list.append({
                "id": task.id,
                "taskName": task.task_name,
                "taskStatus": taskStatus,
                "taskCron": task.task_cron,
                "taskArgs": task.task_args,
                "jobId": task.jobId,
                "projectId": task.projectId
            })

        return restful.success(data=tasks_list)

    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('taskCron', required=True, type=str)
        parser.add_argument('taskName', required=True, type=str)
        parser.add_argument('projectId', required=True, type=int)
        parser.add_argument('taskArgs', required=True, type=list)
        parser.add_argument('enterStatus', required=True, type=int)  # 0新增 1修改 2删除 3停止 4启动
        parser.add_argument('userId', required=True, type=int)
        parser.add_argument('taskType', required=True, type=int)  # 0接口定时任务, 1测试集定时任务, 2项目定时任务,

        args = parser.parse_args()

        task_cron = args["taskCron"]
        task_name = args["taskName"]
        task_args = args["taskArgs"]
        task_type = args["taskType"]
        projectId = args["projectId"]
        userId = args["userId"]

        jobId = str(projectId) + "_" + task_name

        # "? ? ? ? ? ?" #年月日时分秒, 不配置是问号
        crons = str(task_cron).split(" ")

        # TODO 请求添加定时任务时，预估狂调用时间是否可以完成接口。 例如一个接口3秒，定时任务不可以小于3秒执行一次
        if task_cron is None or len(crons) != 6:
            return restful.params_error("cron配置有误")
        else:
            second = crons[5] if crons[5] != "?" else None
            minute = crons[4] if crons[4] != "?" else None
            hour = crons[3] if crons[3] != "?" else None
            day = crons[2] if crons[2] != "?" else None
            month = crons[1] if crons[1] != "?" else None
            year = crons[0] if crons[0] != "?" else None
            cron_dict = {
                "second": second,
                "minute": minute,
                "hour": hour,
                "day": day,
                "month": month,
                "year": year
            }

        enter_status = args["enterStatus"]
        task = AlterTasks.query.filter(AlterTasks.jobId == jobId).first()
        scheduler = APScheduler()

        if enter_status == 0:  # 新增
            if task is not None:
                return restful.params_error("定时任务已存在")

            task = AlterTasks(jobId=jobId, task_name=task_name, task_cron=task_cron, projectId=projectId,
                              task_args=json.dumps(task_args), task_type=task_type, userId=userId)
            db.session.add(task)
            message = "添加成功"

        elif enter_status == 1:  # 修改
            task.task_name = task_name
            task.task_cron = task_cron
            task.projectId = projectId
            task.task_args = task_args
            message = "修改成功"

        if enter_status == 1 or enter_status == 0:
            task_args = (task_type, jobId, projectId, task_args)
            scheduler.add_job(jobId, run_task, task_args, cron_dict, trigger='cron')

        if enter_status == 2:  # 删除
            task.is_delete = 1
            scheduler.remove_job(jobId)
            message = "删除成功"

        elif enter_status == 3:
            task.task_status = 1  # 暂停
            scheduler.pause_job(jobid=jobId)
            message = "暂停成功"

        elif enter_status == 4:
            task.task_status = 0  # 开启
            scheduler.resume_job(jobid=jobId)
            message = "开启成功"

        db.session.commit()
        return restful.success(message=message)


api.add_resource(TaskOperation, '/taskOperation')


class HostManage(Resource):
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('name', required=False, type=str)  # 名字
        parser.add_argument('host', required=False, type=str)  # 地址
        parser.add_argument('environmentId', required=False, type=int)  # 环境Id
        parser.add_argument('hostId', required=False, type=int)  # 环境Id
        parser.add_argument('typeStatus', required=True, type=int)  # 0新增，1修改，2删除
        args = parser.parse_args()
        type_status = args["typeStatus"]

        name = args["name"]
        host = args["host"]
        environmentId = args["environmentId"]
        hostId = args["hostId"]

        if type_status == 0:
            hostObj = AlterHost(environmentId=environmentId, name=name, host=host)
            db.session.add(hostObj)

        elif type_status == 1:
            hostObj = AlterHost.query.filter(AlterHost.id == hostId).first()
            hostObj.name = name
            hostObj.host = host

        elif type_status == 2:
            hostObj = AlterHost.query.filter(AlterHost.id == hostId).first()
            hostObj.is_delete = 1

        db.session.commit()
        return restful.success("成功")


api.add_resource(HostManage, '/hostManage')


@common.route("/getEnvironment/")
def get_environment():
    relust = []
    for environment in AlterEnvironment.query.all():
        relust.append({"value": environment.id, "label": environment.environmentName})
    return restful.success(data=relust)


SecondaryFileType = {
    "0": "支付文件",
    "1": "退款文件",
    "2": "确认收货"
}


@common.route("/getSecondaryFiles/")
def get_secondary_files():
    """
    获取二清文件列表
    :return:
    """
    relust = []
    for file in SecondaryFile.query.filter(SecondaryFile.is_delete == 0).all():
        relust.append({"fileId": file.id, "filePath": file.file_path, "typeName": SecondaryFileType[file.type],
                       "fileName": file.file_name})
    return restful.success(data={
        "fileData": relust
    })


@common.route("/secondary_upload/", methods=['POST'])
def secondary_upload():
    """
    二清文件上传 分析，
    支付，退款，确认收货
    """
    file = request.files['file']
    filename = file.filename
    if not filename.endswith(".txt"):
        return restful.params_error("请上传txt文件")

    secondary_url = os.path.join(config.UPLOAD_SECONDARY, filename)
    file.save(secondary_url)
    _type = 999
    if str(filename).find("C19_BOOKPAYDETAIL") != -1:
        _type = 0
    if str(filename).find("C19_BOOKPAYREFUND") != -1:
        _type = 1
    if str(filename).find("C19_BOOKAFFIRM") != -1:
        _type = 2
    if _type == 999:
        return restful.params_error("文件类型不对")

    """
    C19_BOOKPAYDETAIL 支付 0
    C19_BOOKPAYREFUND 退款 1
    C19_BOOKAFFIRM 确认收货 2
    """

    db.session.add(SecondaryFile(file_path=secondary_url, type=_type, file_name=file.filename))
    db.session.commit()
    return restful.success(message="上传成功")

@common.route("/getHosts/")
def get_hosts():
    """
    获取接口host用于动态配置
    :return:
    """
    environmentId = request.args.get('environmentId')
    relust = []
    for host in AlterHost.query.filter(and_(AlterHost.environmentId == environmentId, AlterHost.is_delete == 0)).all():
        relust.append({"hostId": host.id, "name": host.name, "host": host.host, "environmentId": host.environmentId})
    return restful.success(data={
        "hosts": relust,
        "hostsCols": hostsCols
    })


@common.route("/deleteCatalogue")
def delete_catalogue():
    catalogueId = request.args.get('catalogueId')
    params = AlterParams.query.filter(and_(AlterParams.catalogueId == catalogueId, AlterParams.is_delete == 0)).first()
    if params is not None:
        return restful.params_error("有接口无法删除")
    else:
        catalogueObj = AlterCatalogue.query.filter(AlterCatalogue.id == catalogueId).first()
        if catalogueObj.catalogueId == 0:
            catalogue = AlterCatalogue.query.filter(
                and_(AlterCatalogue.catalogueId == catalogueId, AlterCatalogue.is_delete == 0)).first()
            if catalogue is not None:
                return restful.params_error("有接口无法删除")

        catalogueObj.is_delete = 1
        db.session.commit()
    return restful.success("删除成功")


# @common.route("/getPayRefund/")
# def pay_refund():
#     fileId = request.args.get('fileId')
#     secondarysRelust = []
#     secondarysCols = []
#
#     secondarys = SecondaryFile.query.filter(SecondaryFile.id == fileId).first()
#
#     f = codecs.open(secondarys.file_path, mode='r',
#                     encoding='utf-8')  # 打开txt文件，以‘utf-8'编码读取
#     next(f)
#     line = f.readline()  # 以行的形式进行读取文件
#     while line:
#         a = line.strip().split("|")
#         for index, value in enumerate(a, 0):
#             pay_detail_fields[index]["value"] = value
#         secondarysRelust.append(copy.deepcopy(pay_detail_fields))
#         line = f.readline()
#     f.close()
#
#     for pay_detail_field in pay_detail_fields:
#         secondarysCols.append({
#             "label": pay_detail_field["field"] + "(" + pay_detail_field["required"] + ")" + pay_detail_field[
#                 "describe"],
#             "value": pay_detail_field
#         })
#
#     return restful.success(data={
#         "secondarysRelust": secondarysRelust,
#         "secondaryCols": secondarysCols
#     })


@common.route("/getReports")
def get_reports():
    page_index = int(request.args.get('page_index'))
    page_size = 12
    relust = []
    count = AlterExecuteLog.query.count()
    executes = AlterExecuteLog.query.paginate(page_index, page_size, error_out=False)
    for execute in executes.items:
        relust.append({
            "caseId": execute.caseId,
            "create_time": execute.create_time.strftime('%Y-%m-%d %H:%M:%S'),
            "source": "手动运行" if execute.source == '0' else "定时任务",
            "is_read": "已阅读" if execute.is_read == '0' else "待阅读",
            "logType": execute.log_type,
            "amount": execute.amount,
            "error_num": execute.error_num,
            "time": execute.time
        })

    return restful.success(data={
        "relust": relust,
        "pageCount": count / page_size * 10,
        "countNum": count
    })


"""
执行查询SQL
"""


@common.route("/runSql")
def run_sql():
    sql = request.args.get('sql')
    interceptor = request.args.get('interceptor')

    sqlsTableDatas = []
    actualCols = []

    try:
        db_test = gat_db_object(interceptor)
        sqlsTableDatas, actualCols = db_test.fetchall_new(sql)

    except Exception as e:
        current_app.logger.error("controller.common.views.run_sql --> sql:{sql} , e:{e}".format(sql=g.sql, e=repr(e)))

        return restful.params_error(data=
        {
            "sqlsTableDatas": sqlsTableDatas,
            "actualCols": actualCols
        }, message="SQL语法错误")

    return restful.success(data=
    {
        "sqlsTableDatas": sqlsTableDatas,
        "actualCols": actualCols
    }, message="获取成功")


"""
获取动态参数
"""


@common.route("/getDynamic")
def run_dynamic():
    return restful.success()


@common.route("/swarm", methods=['POST'])
def swarm():
    from requests_toolbelt import MultipartEncoder
    parser = reqparse.RequestParser()
    parser.add_argument('locust_count', required=True, type=int)
    parser.add_argument('hatch_rate', required=True, type=int)
    parser.add_argument('host', required=True, type=str)
    args = parser.parse_args()
    # setting["host"] = str(args["host"])
    try:
        import os
        systemStr = "locust -f {file} --host=" + str(args["host"]) + "&"
        print(systemStr.format(file="/usr/local/alter/controller/common/locustfile.py"))
        # os.system("start locust -f controller\common\locustfile.py --host=" + str(args["host"]))
        os.system(systemStr.format(file="/usr/local/alter/controller/common/locustfile.py"))
    except Exception as e:
        print(repr(e))

    finally:
        from threading import Thread

        def startSwarm():
            import time
            time.sleep(3)
            m = MultipartEncoder(fields={
                "locust_count": str(args["locust_count"]),
                "hatch_rate": str(args["hatch_rate"]),
                "host": str(args["host"])
            })
            print(requests.post(url="http://localhost:8089/swarm", data=m, headers={'Content-Type': m.content_type}))

        Thread(target=startSwarm).start()
    return restful.success()


@common.route("/getRequests/")
def get_requests():
    return restful.success(data={
        "datas": requests.get("http://localhost:8089/stats/requests").json(),
        "props": [
            {
                "prop": "method",
                "label": "请求"
            },
            {
                "prop": "name",
                "label": "接口地址"
            },
            {
                "prop": "num_requests",
                "label": "请求数量"
            },
            {
                "prop": "num_failures",
                "label": "请求错误"
            },
            {
                "prop": "median_response_time",
                "label": "平均耗时 (ms)"
            },
            {
                "prop": "ninetieth_response_time",
                "label": "90%ile (ms)"
            },
            {
                "prop": "avg_response_time",
                "label": "Average (ms)"
            },
            {
                "prop": "min_response_time",
                "label": "Min (ms)"
            },
            {
                "prop": "max_response_time",
                "label": "Max (ms)"
            },
            {
                "prop": "avg_content_length",
                "label": "Average size (bytes)"
            },
            {
                "prop": "current_rps",
                "label": "Current RPS"
            },
            {
                "prop": "current_fail_per_sec",
                "label": "Current Failures/s"
            }
        ]
    })


@common.route("/getProjectDiffs")
def get_project_diffs():
    projectId = request.args.get('projectId')
    from_branch = request.args.get('from_branch')
    to_branch = request.args.get('to_branch')

    return restful.success(gitlab_utils.get_project_diffs(projectId, from_branch, to_branch))


@common.route("/getGitLabProjects")
def get_gitlab_projects():
    return restful.success(data={
        "projectsDates": gitlab_utils.get_projects(),
        "projectsCols":[
            {
                "label": "id"
            },
            {
                "label": "name"
            }
        ]
    })



@common.route("/clearCarInventory",methods=['POST'])
def clearCarInventory():
    interceptor = request.args.get('environment') #环境
    sqldb = gat_db_object(interceptor)
    redis = get_redis_object(interceptor)
    carNo = request.json.get("carNo")
    if carNo:
        # 拼装sql后执行
        transFilter = f"delete from atzuchedb.trans_filter where car_no = {carNo}"
        carFilter = f"delete from atzuchedb.car_filter where car_no = {carNo}"
        sqldb.execute_sql(transFilter)
        sqldb.execute_sql(carFilter)
        # 拼装rediskey后执行
        rediskey_holiday = f"carservice:cartime:holidaytime:carno{carNo}"
        rediskey_filter = f"carservice:cartime:filtercar:carno{carNo}"
        rediskey_notake = f"carservice:cartime:notakecar:carno{carNo}"
        rediskey_norent = f"carservice:cartime:norentcar:carno{carNo}"
        redis.delete(rediskey_holiday)
        redis.delete(rediskey_filter)
        redis.delete(rediskey_notake)
        redis.delete(rediskey_norent)
        return restful.success("清除库存成功")
    else:
        return restful.params_error("车辆号不能为空")
