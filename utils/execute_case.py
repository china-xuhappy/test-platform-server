"""
执行接口自动化用例类

"""
import copy
import json
import time

from bson import json_util
from flask import current_app, g
from sqlalchemy import and_

from controller.project.models import AlterFlow, AlterParams, AlterFiles
from exts import executor, mongo
from utils.request_utils import run_tests


def execute_flow_case(app, flows, kwargs):
    """
    执行flow 下面的用例， 传入需要执行的用例
    :param flows: 需要执行的用例集
    :param kwargs: 别的参数
    :return:
    """
    projectId = kwargs["projectId"]
    gatherId = kwargs["gatherId"]
    caseId = kwargs["caseId"]
    userObj = kwargs["userObj"]
    isMail = kwargs["isMail"]
    environment = kwargs["environment"]
    flowParams = []

    with app.app_context():
        files = []
        for file in AlterFiles.query.filter(
                and_(AlterFiles.project_id == projectId, AlterFiles.is_delete == 0)).all():
            files.append(file.file_name)

        for flow in flows:
            flow = AlterFlow.query.filter(AlterFlow.id == flow["flowId"]).first()
            run_results = mongo.db.flowParameters.find_one({"flowId": flow.id})
            mongo_data = json.loads(json_util.dumps(run_results))
            paramsId = flow.paramsId
            param = AlterParams.query.filter(AlterParams.id == paramsId).first()
            param.flows = {
                "flowInitialTests": mongo_data["initialTests"],
                "gatherId": flow.gatherId,
                "flowId": flow.id,
                "parameters": json.loads(flow.parameters),
                "flowUseDatas": mongo_data["dynamicVariable"],
                "flowName": flow.name,
                "flowRests": json.loads(flow.rests),
            }
            param.files = files
            param.projectId = projectId
            flowParams.append(copy.deepcopy(param))

        local_id = str(projectId) + "_" + str(gatherId)
        local_id = caseId + "_" + local_id
        return run_tests(interfaceParams=flowParams, rests={
            "local_id": local_id,
            "caseId": caseId,
            "environment": environment,
            "source": 0,
            "projectId": projectId,
            "userDatas": userObj.useDatas if userObj is not None else [],
            "userId": userObj.id if userObj is not None else 3,
            "isMail": isMail,
            "gatherId": gatherId
        })
