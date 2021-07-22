#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @File  : assert_utils.py
# @Author: kaixin.xu
# @Date  : 2019/12/11
# @Desc  : 断言类
from flask import current_app

from utils.variable_utils import get_str_dynamic


def assertEqual(a, b):
    try:
        assert a == b
        return True
    except Exception as e:
        current_app.logger.error("utils.assert_utils.assertEqual -> 断言失败 实际 :" + str(b) + "，预期: " + str(a))
        return False


"""
a 预计
b 实际
True 断言成功，
False 断言失败
"""


def assertEqualDict(a, b, local_id=None, files=None):
    # print(a)
    # print(b)
    isError = True

    if type(a) != type(b):
        isError = False

    if isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            isError = False

        for i in range(len(a)):
            a[i]["results"] = {}
            results = a[i]["results"]
            try:
                if i >= len(b):
                    actual = {}
                else:
                    actual = b[i]
                assert_result = assertEqualDict(a[i], actual, local_id=local_id, files=files)
            except Exception as e:
                assert_result = False
                current_app.logger.error(
                    "utils.assert_utils.assertEqualDict -> 断言失败 实际 :" + str(actual) + "，预期: " + results)

            if not assert_result:
                results["result"] = "失败"
                results["type"] = "danger"
                isError = False
            else:
                results["result"] = "成功"
                results["type"] = "success"

    elif isinstance(a, dict) and isinstance(b, dict):
        for key, value in a.items():
            if key in ["results"]:  # 过滤
                continue

            # 防止数据库None判断， 都搞成空字符串
            expect_value = a[key]["value"]
            actual_value = "999999999"
            if key in b:
                actual_value = b[key]["value"]

            expect_value = str(expect_value)
            actual_value = str(actual_value)

            expect_value = get_str_dynamic(expect_value, local_id=local_id, files=files)

            if not assertEqual(expect_value, actual_value):
                a[key]["status"] = 1  # 失败
                isError = False
            else:
                a[key]["status"] = 0  # 成功
            a[key]["value"] = expect_value
    else:
        isError = False

    return isError
