#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @File  : task_utils.py
# @Author: kaixin.xu
# @Date  : 2020/4/5
# @Desc  : 定时任务工具类， 用来跑定时任务 --- 待完成

"""
跑接口用例的定时任务,
参数list
"""
import threading
from flask import g, current_app
import time, copy
from .request_utils import run_tests
from controller.project.models import AlterParams
from exts import scheduler


def run_task(taskType, jobId, projectId, args):
    with scheduler.app.app_context():
        if taskType == 0:
            run_interface(jobId, args, projectId)


def run_interface(jobId, interfaceIds, projectId):
    params = []
    for interfaceId in interfaceIds:
        param = AlterParams.query.filter(AlterParams.interfaceId == interfaceId).first()
        params.append(copy.deepcopy(param))

    local_id = str(jobId)

    app = current_app._get_current_object()
    caseId = "Task" + str((int(round(time.time() * 1000))))  # 报告id

    local_id = caseId + "_" + local_id
    if "environment" in g:
        environment = g.environment
    else:
        environment = 2

    threading.Thread(target=run_tests, args=(app, params, {
        "local_id": local_id,
        "caseId": caseId,
        "environment": environment,
        "source": 1,
        "projectId": projectId
    })).start()
