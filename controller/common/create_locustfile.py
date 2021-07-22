#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @File  : create_locustfile.py
# @Author: kaixin.xu
# @Date  : 2019/12/13
# @Desc  : 创建locustfile
import os

def createLocust(host,method,route,params):
    if method == 'get':
        params = ''
    src, _ = os.path.split(os.path.realpath(__file__))
    with open(os.path.join(src,"locustfile.py"),"w",encoding="utf-8") as f:
        f.write("""
from locust import HttpLocust, TaskSet, task
class WebsiteTasks(TaskSet):

    @task(1)
    def about(self):
        self.client.{method}("{route}"{params})
        
class WebsiteUser(HttpLocust):
    task_set = WebsiteTasks
    host = "{host}"
    min_wait = 1000
    max_wait = 5000
    stop_timeout = 60""".format(method=method,route=route,params=params,host=host))
        f.close()
