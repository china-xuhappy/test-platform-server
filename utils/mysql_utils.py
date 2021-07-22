#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @File  : mysql_utils.py
# @Author: kaixin.xu
# @Date  : 2019/12/24
# @Desc  : MySQL工具类

import pymysql
import logging
import sys

class DBHelper:
    # 构造函数
    def __init__(self, host, user, pwd):
        self.host = host
        self.user = user
        self.pwd = pwd
        self.conn = None
        self.cur = None

    # 连接数据库
    def connectDatabase(self):
        try:
            self.conn = pymysql.connect(self.host, self.user,
                                        self.pwd, charset='utf8')
        except:
            return False
        self.cur = self.conn.cursor()
        return True

    # 关闭数据库
    def close(self):
        # 如果数据打开，则关闭；否则没有操作
        if self.conn and self.cur:
            self.cur.close()
            self.conn.close()
        return True

    # 执行数据库的sq语句,主要用来做插入操作
    def execute_sql(self, sql, params=None):
        # 连接数据库
        self.connectDatabase()
        try:
            if self.conn and self.cur:
                # 正常逻辑，执行sql，提交操作
                self.cur.execute(sql, params)
                self.conn.commit()
        except:
            self.close()
            return False
        return True

    # 用来查询表数据
    def fetchall(self, sql, params=None):
        self.execute_sql(sql, params)
        cols = self.cur.description
        results = self.cur.fetchall()

        actualDatas = []
        a = 0
        for result in results:
            a += 1

            for i in range(len(result)):
                if a >= 2:
                    if result[i] is None:
                        continue
                    fieldValue = actualDatas[i]["fieldValue"]
                    if isinstance(fieldValue, list):
                        fieldValue.append(result[i])
                        actualDatas[i]["fieldValue"] = fieldValue
                        continue
                    actualDatas[i]["fieldValue"] = [actualDatas[i]["fieldValue"], result[i]]
                else:
                    actualDatas.append({
                        "fieldValue": result[i]
                    })

        for i in range(len(cols)):
            actualDatas[i]["fieldName"] = cols[i][0]

        return actualDatas

    # 新的方法， 用来初始化新的数据
    def fetchall_new(self, sql, params=None):
        self.execute_sql(sql, params)
        cols = self.cur.description
        results = self.cur.fetchall()

        actualDatas = []
        for result in results:
            actualDataDict = {}
            for i in range(len(result)):
                actualDataDict[cols[i][0]] = {
                    "value": result[i]
                }
                # actualDataDict["results"] = [{
                #     "result": '待测试',
                #     "type": 'warning'
                # }]
            actualDatas.append(actualDataDict)

        actualCols = []
        for i in range(len(cols)):
            actualCols.append({
                "label" : cols[i][0]
            })

        return actualDatas, actualCols

    def fetchone_sql(self, sql, params=None):
        self.execute_sql(sql, params)
        return self.cur.fetchall()
