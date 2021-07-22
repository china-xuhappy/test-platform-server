#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @File  : views.py
# @Author: kaixin.xu
# @Date  : 2020/3/17
# @Desc  : 用例相关接口
import json
import time

from bson import json_util
from flask import Blueprint, jsonify, g, render_template, request
from flask_restful import Api, Resource, marshal_with, reqparse, fields

case = Blueprint('case', __name__, url_prefix='/case')
from exts import db, mongo
from datetime import datetime

api = Api(case)
from utils import restful
from controller.project.models import AlterCaseGather, AlterFlow
from sqlalchemy import or_, and_


@case.route("/getCaseId")
def get_caseId():
    return restful.success(data="AT" + str((int(round(time.time() * 1000)))))


@case.route("/getCases")
def get_cases():
    """
    获取用例集下面的用例
    排序： 谁大 谁在上面
    """
    gatherId = request.args.get('gatherId')
    flows = AlterFlow.query.order_by(db.desc(AlterFlow.sort)).filter(
        and_(AlterFlow.gatherId == gatherId, AlterFlow.is_delete == 0)).all()
    rest_datas = []
    for flow in flows:
        flowId = flow.id
        paramsId = flow.paramsId
        name = flow.name
        params = flow.params
        rest_datas.append({
            "flowId": flowId,
            "paramsId": paramsId,
            "flowName": name,
            "params": {
                "id": params.id,
                "describe": params.describe,
            }
        })

    return restful.success(data=rest_datas)


@case.route("/deleteCases", methods=["POST"])
def delete_cases():
    parser = reqparse.RequestParser()
    parser.add_argument('flowId', required=False, type=int)
    args = parser.parse_args()
    flows = AlterFlow.query.filter(AlterFlow.id == args["flowId"]).first()
    flows.is_delete = 1
    db.session.commit()

    return restful.success()


@case.route("/topCases", methods=["POST"])
def top_cases():
    """
    用例上升排序
    :return:
    """
    parser = reqparse.RequestParser()
    parser.add_argument('flowId', required=False, type=int)
    parser.add_argument('gatherId', required=False, type=int)
    args = parser.parse_args()
    gatherId = args["gatherId"]

    # 自己加一下
    flowOneself = AlterFlow.query.filter(args["flowId"] == AlterFlow.id).first()
    flowOneself.update_time = datetime.now()
    oldSort = flowOneself.sort

    # 找到自己加一下的别人，减一
    flowOther = AlterFlow.query.order_by(db.asc(AlterFlow.sort)).filter(
        db.and_(AlterFlow.gatherId == gatherId, AlterFlow.is_delete == 0, AlterFlow.sort > flowOneself.sort)).first()
    if flowOther is None:
        return restful.success(message="最顶端了")

    flowOneself.sort = flowOther.sort
    flowOther.sort = oldSort
    flowOther.update_time = datetime.now()

    db.session.commit()
    return restful.success(message="上升成功")


class CaseGatherOperation(Resource):
    """
        用例集
    """

    resource_fields = {
        "id": fields.Integer,
        "gatherName": fields.String,
        "totalPages": fields.Integer
    }

    @marshal_with(resource_fields)
    def get(self):
        projectId = int(request.args.get('projectId'))
        page_index = int(request.args.get('page_index'))
        page_size = 9999

        case_gather = AlterCaseGather.query.filter(AlterCaseGather.projectId == projectId).paginate(page_index,
                                                                                                    page_size,
                                                                                                    error_out=False)
        return case_gather.items

    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('gatherName', required=False, type=str)
        parser.add_argument('projectId', required=False, type=int)
        args = parser.parse_args()
        gather = AlterCaseGather(gatherName=args["gatherName"], projectId=args["projectId"])
        db.session.add(gather)
        db.session.commit()
        return restful.success()


api.add_resource(CaseGatherOperation, '/caseGatherOperation')
