#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @File  : views.py
# @Author: kaixin.xu
# @Date  : 2020/3/17
# @Desc  : 项目相关接口

import math
from concurrent.futures._base import as_completed
from concurrent.futures.thread import ThreadPoolExecutor

import requests
from flask import Blueprint, request, g, current_app, make_response, send_from_directory
from flask_restful import Api, Resource, marshal_with, reqparse, fields

from utils.execute_case import execute_flow_case

project = Blueprint('project', __name__, url_prefix='/project')
from utils import restful
from exts import db, mongo, mail

api = Api(project)
from .models import AlterProject, \
    AlterInterface, AlterParams, \
    AlterFlow, AlterExecuteLog, AlterUser, AlterCatalogue, AlterCaseGather, AlterFiles
from sqlalchemy import and_
import time
import json
from bson import json_util
from utils.variable_utils import userVariableDict
from sqlalchemy import func


@project.route("/deleteProject", methods=['POST'])
def delete_project():
    """
    删除项目
    :return:
    """
    parser = reqparse.RequestParser()
    parser.add_argument('projectId', required=True, type=int)
    parser.add_argument('userId', required=True, type=int)
    args = parser.parse_args()

    project = AlterProject.query.filter(AlterProject.id == args["projectId"]).first()
    project.is_delete = 1
    db.session.commit()

    return restful.success(message="删除成功")


@project.route("/getProjects")
def get_projects():
    # resource_fields = {
    #     "id": fields.Integer,
    #     "projectName": fields.String,
    #     "project_type": fields.String,
    #     "users": fields.Nested({
    #         "username": fields.String
    #     }),
    #     "python_files": fields.Nested({
    #         "file_name": fields.String
    #     }),
    # }

    # projectType = request.args.get('type')
    results = []
    for project in AlterProject.query.filter(AlterProject.is_delete == 0).all():
        projectId = project.id
        alter_files = []

        for alter_file in AlterFiles.query.filter(
                and_(AlterFiles.is_delete == 0, AlterFiles.project_id == projectId)).all():
            alter_files.append({
                "file_name": alter_file.file_name
            })

        results.append({
            "id": projectId,
            "projectName": project.projectName,
            "project_type": project.project_type,
            "python_files": alter_files,
            "users": [],
            "is_read": "否"
        })
    return restful.success(data=results)

    # return AlterProject.query.order_by(db.asc(AlterProject.id)).filter(
    #     and_(AlterProject.project_type == projectType, AlterProject.is_delete == 0)).all()


class ProjectManage(Resource):
    """
    项目类 添加 编辑项目，获取项目
    """

    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('dutyPerson', required=True, type=list)  # 负责人
        parser.add_argument('projectName', required=True, type=str)  # 项目名
        parser.add_argument('isPrivate', required=True)  # 是否私有 0不是, 1私有
        parser.add_argument('pythonFiles', required=False, type=list)  # 函数Python文件
        parser.add_argument('isEdit', required=True, type=int)  # 0新增，1编辑
        parser.add_argument('projectId', required=False, type=int)  #

        args = parser.parse_args()
        is_edit = args["isEdit"]
        projectId = args["projectId"]
        python_files = args["pythonFiles"]
        projectName = args["projectName"]
        dutyPerson = args["dutyPerson"]
        if is_edit == 0:
            project = AlterProject(projectName=projectName)

            for duty in dutyPerson:
                user = AlterUser.query.filter(AlterUser.id == duty).first()
                user.projects.append(project)
                db.session.add(user)

            db.session.add(project)
            db.session.commit()
            for file_name in python_files:
                alter_file = AlterFiles.query.filter(
                    and_(AlterFiles.file_name == file_name, AlterFiles.project_id == project.id)).first()
                if alter_file is None:
                    db.session.add(AlterFiles(project_id=project.id, file_name=file_name))

            db.session.commit()
        elif is_edit == 1:
            project = AlterProject.query.filter(AlterProject.id == projectId).first()
            if project is not None:
                project.projectName = projectName

            alter_files = AlterFiles.query.filter(
                and_(AlterFiles.project_id == projectId, AlterFiles.is_delete == 0)).all()
            if alter_files is not None:
                for alter_file in alter_files:
                    alter_file.is_delete = 1
                db.session.commit()

            for file_name in python_files:
                alter_file = AlterFiles.query.filter(
                    and_(AlterFiles.file_name == file_name, AlterFiles.project_id == projectId,
                         AlterFiles.is_delete == 0)).first()
                if alter_file is None:
                    db.session.add(AlterFiles(project_id=project.id, file_name=file_name))
            db.session.commit()

        return restful.success()


# 弃用
# @project.route("/savaFlows", methods=['POST'])
# def sava_flows():
#     parser = reqparse.RequestParser()
#     parser.add_argument('flows', required=True, type=list)
#     args = parser.parse_args()
#
#     for flow in args["flows"]:
#         flowObj = AlterFlow.query.filter(AlterFlow.id == flow["id"]).first()
#         useDatas = str(json.dumps(obj=flow["params"]["useDatas"], ensure_ascii=False))
#         flowObj.useDatas = useDatas
#         db.session.commit()
#
#     return restful.success()

@project.route("/runFlows", methods=['POST'])
def run_flows():
    """
    执行单个用例集--- 可在用例集选择执行某个用例
    """
    parser = reqparse.RequestParser()
    parser.add_argument('flows', required=True, type=list)
    parser.add_argument('environment', required=False, type=int)
    parser.add_argument('projectId', required=False, type=int)
    parser.add_argument('gatherId', required=False, type=int)
    parser.add_argument('userId', required=True, type=int)
    parser.add_argument('caseId', required=False, type=str)

    args = parser.parse_args()
    run_time = time.perf_counter()
    userObj = AlterUser.query.filter(AlterUser.id == args["userId"]).first()

    environment = args["environment"]
    flows = args["flows"]
    if flows is None:
        return restful.params_error("请选择要执行的接口")

    if "caseId" in args and args["caseId"] is not None:
        caseId = args["caseId"]
    else:
        caseId = "AT" + str((int(round(time.time() * 1000))))  # 报告id
    userVariableDict.clear()
    app = current_app._get_current_object()
    with ThreadPoolExecutor(max_workers=10) as t:
        obj_list = []
        executorobj = t.submit(execute_flow_case, *(app, flows, {
            "caseId": caseId,
            "projectId": args["projectId"],
            "gatherId": args["gatherId"],
            "userObj": userObj,
            "isMail": True,
            "environment": environment
        }))
        obj_list.append(executorobj)
        for future in as_completed(obj_list):
            data = future.result()

            log = AlterExecuteLog.query.filter(AlterExecuteLog.caseId == caseId).first()
            log.success_num = data["success_num"]
            log.error_num = data["error_num"]
            log.amount = data["amount"]
            ent_time = time.perf_counter()
            if log.time is None or log.time == 0 or log.time == "":
                log.time = math.ceil(ent_time - run_time)

            db.session.commit()

    return restful.success(message="执行完成!!", data=caseId)


@project.route("/runCaseGather", methods=['POST'])
def run_case_gather():
    """
    执行用例集合
    :return:
    """
    data = request.get_data()
    args = json.loads(data.decode("utf-8"))
    run_time = time.perf_counter()
    userObj = AlterUser.query.filter(AlterUser.id == args["userId"]).first()

    environment = args["environment"]
    is_mail = args["mail"]  # 是否发邮件

    caseId = "AT" + str((int(round(time.time() * 1000))))  # 报告id
    app = current_app._get_current_object()
    with ThreadPoolExecutor(max_workers=10) as t:
        obj_list = []
        current_app.logger.info(
            "project.views.run_case_gather -> gathers: {gathers}".format(gathers=args["gathers"]))

        for gather in args["gathers"]:
            flowIds = []
            flows = AlterFlow.query.order_by(db.desc(AlterFlow.sort)).filter(
                and_(AlterFlow.gatherId == gather, AlterFlow.is_delete == 0)).all()
            for flow in flows:
                flowIds.append({"flowId": flow.id, "flowName": flow.name})
            current_app.logger.info(
                "project.views.run_case_gather -> flowIds:{flowIds}".format(flowIds=flowIds))

            executorobj = t.submit(execute_flow_case, *(app, flowIds, {
                "caseId": caseId,
                "projectId": args["projectId"],
                "gatherId": gather,
                "userObj": userObj,
                "isMail": False,
                "environment": environment
            }))
            obj_list.append(executorobj)

            time.sleep(10)
        for future in as_completed(obj_list):
            data = future.result()
            current_app.logger.info(
                "project.views.run_case_gather -> as_completed main:{main}".format(main=data))

            log = AlterExecuteLog.query.filter(AlterExecuteLog.caseId == caseId).first()
            log.success_num += data["success_num"]
            log.error_num += data["error_num"]
            log.amount += data["amount"]
            ent_time = time.perf_counter()

            if log.time is None or log.time == "0":
                log.time = math.ceil(ent_time - run_time)
            db.session.commit()

        # 跑完再发邮件
        if is_mail is not None and int(is_mail) == 1:
            report_url = "http://127.0.0.1/#/reportDetail/{caseId}".format(caseId=caseId)
            headers = {"Content-Type": "text/plain"}
            projectObj = AlterProject.query.filter(AlterProject.id == log.projectId).first()
            send_url = None
            send_data = {
                "msgtype": "markdown",
                "markdown": {
                    "content": "# <font color=\"info\"> 提醒！ 接口自动化用例测试完成！！！ </font>\n" +
                               "> 项目名：<font color=\"info\"> {projectName} </font> \n".format(projectName=projectObj.projectName) +
                               "> 执行人：<font color=\"info\"> {userName} </font> \n".format(userName=userObj.username) +
                               "> 测试耗时：<font color=\"info\"> {time} </font> \n".format(time=log.time) +
                               "> 用例总数：<font color=\"info\"> {amount} </font> 通过：<font color=\"info\"> {success_num} </font> 失败：<font color=\"warning\"> {error_num} </font>\n".format(amount=log.amount,success_num=log.success_num,
                                                                                            error_num=log.error_num) +
                               "> 报告地址：<a href='{report_url}'> {report_url} </a> \n".format(report_url=report_url)
                }
            }
            requests.post(url=send_url, headers=headers, json=send_data)
            mail.send_mail({
                "reportUrl": report_url,
                "success_num": log.success_num,
                "error_num": log.error_num,
                "amount": log.amount
            })

    return restful.success(message="执行完成!!", data=caseId)


class FlowOperation(Resource):
    flow_resource_fields = {
        "name": fields.String,
        "params": fields.Nested({
            "id": fields.Integer,
            "describe": fields.String,
        })
    }

    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('gatherId', required=False, type=int)
        parser.add_argument('name', required=False, type=str)
        parser.add_argument('paramsId', required=False, type=int)
        parser.add_argument('dynamicVariable', required=True, type=list)
        parser.add_argument('initialTests', required=True, type=list)
        parser.add_argument('parameters', required=False, type=list)
        parser.add_argument("rests", required=False, type=dict)
        parser.add_argument("typeStatus", required=False, type=int)  # 0 新增， 1修改， 2只修改 parameters
        parser.add_argument("flowId", required=False, type=int)
        args = parser.parse_args()

        rests = args["rests"]
        if rests is not None or rests == "":
            rests = args["rests"]
        else:
            rests = {"variableName": "", "isVariable": False, "isWaitVariable": False, "waitVlue": 0}  # 初始化

        rests = str(json.dumps(obj=args["rests"], ensure_ascii=False))
        parameters = str(json.dumps(obj=args["parameters"], ensure_ascii=False))
        dynamicVariable = args["dynamicVariable"]
        initialTests = args["initialTests"]

        type_status = args["typeStatus"]
        flow = AlterFlow.query.filter(AlterFlow.id == args["flowId"]).first()
        if type_status == 0 and flow is None:
            flowOther = db.session.query(func.min(AlterFlow.sort).label('sort')).filter(
                db.and_(AlterFlow.gatherId == args["gatherId"], AlterFlow.is_delete == 0)).first()
            sort = 999
            if flowOther.sort is not None:
                sort = int(flowOther.sort) - 1

            flow = AlterFlow(gatherId=args["gatherId"], name=args["name"], paramsId=args["paramsId"], rests=rests,
                             sort=sort)
            db.session.add(flow)
            db.session.commit()

            mongo.db.flowParameters.insert_one(
                {
                    "initialTests": initialTests,
                    "dynamicVariable": dynamicVariable,
                    "flowId": flow.id,
                    "gatherId": args["gatherId"]
                }
            )
            return restful.success()

        elif type_status == 1:
            flow.rests = rests
            flow.name = args["name"]

            mongo.db.flowParameters.update(
                {
                    "flowId": flow.id
                },
                {
                    "$set": {
                        "initialTests": initialTests,
                        "dynamicVariable": dynamicVariable
                    }
                }
            )

        elif type_status == 2:
            flow.parameters = parameters

        db.session.commit()
        return restful.success()


@project.route("/getRunLog")
def run_log():
    caseId = request.args.get('caseId')
    page = request.args.get('page')
    gatherId = request.args.get("gatherId")
    if gatherId is not None:
        gatherId = int(gatherId)
    execute = AlterExecuteLog.query.filter(AlterExecuteLog.caseId == caseId).first()
    page_size = 12
    if page is not None:
        page = int(page)

    if page is None or page == 1:
        start = 0
    else:
        start = math.floor(page * 12 / 2)

    if gatherId is not None and gatherId != 0:
        caseCount = mongo.db.runLog.find({"caseId": caseId, "gatherId": gatherId}).count()
        run_results = mongo.db.runLog.find({"caseId": caseId, "gatherId": gatherId}).sort("gatherId").skip(start).limit(
            page_size)
    else:
        caseCount = mongo.db.runLog.find({"caseId": caseId}).count()
        run_results = mongo.db.runLog.find({"caseId": caseId}).sort("gatherId").skip(start).limit(page_size)
    data = json.loads(json_util.dumps(run_results))
    if execute is None:
        return restful.success(data=data)
    else:
        projectObj = AlterProject.query.filter(AlterProject.id == execute.projectId).first()
        projectName = ""
        if projectObj is not None:
            projectName = projectObj.projectName

        gatherIds = str(execute.gatherId).split(",")
        resultGathers = []
        gathers = AlterCaseGather.query.filter(AlterCaseGather.id.in_(gatherIds)).all()
        for gather in gathers:
            resultGathers.append({
                "gatherId": gather.id,
                "gatherName": gather.gatherName
            })

        return restful.success(data={
            "runResults": data,
            "pageCount": caseCount / page_size * 12,
            "executeResult": {
                "successNum": execute.success_num,
                "errorNum": execute.error_num,
                "amountNum": execute.amount,
                "skipNum": 0
            },
            "caseLogObject": {
                "projectName": projectName,
                "caseDate": execute.create_time.strftime("%Y-%m-%d %H:%M:%S"),
                "caseTime": execute.time,
                "amount": execute.amount,
                "error_num": execute.error_num,
                "success_num": execute.success_num,
            },
            "resultGathers": resultGathers
        })


@project.route("/runProject")
def run_project():
    projectId = request.args.get('projectId')
    interfaceParams = AlterParams.query.filter(AlterParams.projectId == projectId).all()

    # run_tests(interfaceParams)
    # db.session.commit()
    return restful.success(message="弃用!!")


# 做项目的添加，和获取
class CatalogueOperation(Resource):
    resource_fields = {
        "id": fields.Integer,
        "catalogueName": fields.String,
        "sonCatalogues": fields.Nested({
            "id": fields.Integer,
            "catalogueName": fields.String,
            "count": fields.Integer,
            "params": fields.Nested({
                "id": fields.Integer,
                "describe": fields.String,
                "method": fields.String,
                "flag": fields.String,
            })
        })
    }

    def post(self):  # add
        parser = reqparse.RequestParser()
        parser.add_argument('catalogueName', required=True, type=str)  # 目录名
        parser.add_argument('projectId', required=True, type=int)
        parser.add_argument('catalogueId', required=True, type=int)  # 目录ID，二级目录用的
        parser.add_argument('currentCatalogueId', required=False, type=int) #当前操作Id，必须修改的时候
        parser.add_argument('type', required=False, type=int)
        args = parser.parse_args()
        catalogueName = args["catalogueName"]
        if args["type"] == 1:
            db.session.add(AlterCatalogue(catalogueName=args["catalogueName"], projectId=args["projectId"],
                                      catalogueId=args["catalogueId"]))
        elif args["type"] == 2:
            catalogue = AlterCatalogue.query.filter(AlterCatalogue.id == args["currentCatalogueId"]).first()
            catalogue.catalogueName = catalogueName

        db.session.commit()
        return restful.success("添加成功")

    @marshal_with(resource_fields)
    def get(self):  # get
        projectId = request.args.get('projectId')
        catalogues = AlterCatalogue.query.filter(
            and_(AlterCatalogue.projectId == projectId, AlterCatalogue.is_delete == 0,
                 AlterCatalogue.catalogueId == 0)).all()
        for catalogue in catalogues:
            sonCatalogues = AlterCatalogue.query.filter(
                and_(AlterCatalogue.projectId == projectId, AlterCatalogue.is_delete == 0,
                     AlterCatalogue.catalogueId == catalogue.id)).all()

            for sonCatalogue in sonCatalogues:
                params = sonCatalogue.params
                for param in params[:]:
                    if param.is_delete == 1:
                        params.remove(param)

                sonCatalogue.count = len(params)
            catalogue.sonCatalogues = sonCatalogues

        return catalogues


api.add_resource(CatalogueOperation, '/catalogueOperation')
api.add_resource(FlowOperation, '/flowOperation')
api.add_resource(ProjectManage, '/projectManage')


@project.route("/getProjectMsg")
def get_project_msg():
    """
    获取项目信息
    :return:
    """
    projectId = request.args.get('projectId')
    count = AlterInterface.query.filter(AlterInterface.projectId == projectId).count()

    return restful.success(data={
        "count": count
    })
