"""
Excel 工具类, 主要是导入测试用例
把功能测试用例 转化自动化测试用例
"""
import xlrd
from sqlalchemy import func

from exts import db
from ui_controller.case.models import UiCase, UiStep
from ui_controller.element.models import UiActivitys, UiElements

gactivityId = None  # 切换页面才会变
activity_name = ""
sorts = 999


def case_step_conversion(step, caseId):
    """测试步骤转换"""
    global gactivityId, activity_name, sorts
    steps = str(step).split(",")

    for step in steps:
        stepOther = db.session.query(func.min(UiStep.sort).label('sort')).filter(
            db.and_(UiStep.caseId == caseId, UiStep.is_delete == 0)).first()

        if stepOther.sort is not None:
            sorts = int(stepOther.sort) - 1

        dot = step.find(".")
        colon = step.find(":")
        stepNo = step[: dot]  # 编号
        operation = step[dot + 1: colon]  # 操作方式

        element_name, content = None, None
        elementId = None
        activityId = gactivityId
        if operation != "左滑" and operation != "右滑" and operation != "上滑" and operation != "下滑" and operation != "返回":

            if operation != "跳转" and operation != "切换" and operation != "输入":
                element_name = step[colon + 1:]

            if operation == "输入":
                element_name = step[colon + 1: step.find("(")]
                content = step[step.find("(") + 1: -1]

            if operation == "切换":
                operation = "切换界面"
                activity_name = step[colon + 1:]
                activity = UiActivitys.query.filter(UiActivitys.activity_name == activity_name).first()
                if activity is not None:
                    gactivityId = activity.id
                    activityId = gactivityId

            elif operation == "跳转":
                operation = "断言跳转"
                activity_name = step[colon + 1:]
                activity = UiActivitys.query.filter(UiActivitys.activity_name == activity_name).first()
                if activity is not None:
                    activityId = activity.id

            if activityId is None:
                continue

            if operation != "断言跳转" and operation != "切换界面":
                element = UiElements.query.filter(UiElements.element_name == element_name).first()
                if element is None:
                    continue
                else:
                    elementId = element.id

        db.session.add(UiStep(operation=operation, caseId=caseId, elementId=elementId, activityId=activityId,
                              content=content, sort=sorts))
        db.session.commit()
        print(stepNo, operation, activity_name, element_name, content)


def import_ui_case(file, projectId):
    """
    用例 导入 成UI自动化用例
    :return:
    """
    wb = xlrd.open_workbook(file_contents=file)

    sheet1 = wb.sheet_by_index(0)  # 通过索引获取表格
    print(sheet1.name, sheet1.nrows, sheet1.ncols)
    nrows = sheet1.nrows
    gcase_name = ""
    global sorts
    clos = sheet1.col_values(0)
    for clo in clos:
        caseObj = UiCase.query.filter(UiCase.case_name == clo).first()
        if caseObj is not None:
            steps = UiStep.query.filter(UiStep.caseId == caseObj.id).all()
            for step in steps:
                step.is_delete = 1
    db.session.commit()
    for i in range(nrows):
        title = sheet1.row_values(i)  # 第0个是title
        if i != 0:
            rows = sheet1.row_values(i)  # 获取行内容
            case_name = rows[0]  # 功能模块，一个模块是一个用例。 用例下面有多个步骤
            caseId = rows[1]  # 用例编号
            case_step = rows[2]  # 测试步骤
            case_expect = rows[3]  # 预期结果

            if case_name != "":
                gcase_name = case_name

            caseObj = UiCase.query.filter(UiCase.case_name == gcase_name).first()
            if caseObj is None:
                caseObj = UiCase(case_name=case_name, describe="", projectId=projectId)
                db.session.add(caseObj)
                db.session.commit()
                sorts = 999

            case_step_conversion(case_step, caseObj.id)
            case_step_conversion(case_expect, caseObj.id)
