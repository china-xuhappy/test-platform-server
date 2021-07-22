#!/usr/bin/env python
# _*_ coding: utf-8 _*_
# @Time : 2021/1/29 13:54
# @Author : liujianxiao
# @Version：V 0.1
# @File : test_xml.py
# @desc : xml解析

import xml

class TestDemo():
    def test_case1(self):
        dom = xml.dom.minidom.parse("test.xml")
        root = dom.documentElement
        movies = root.getElementsByTagName("movie")
        for movie in movies:
            nodes = movie.childNodes
            for node in nodes:
                # print(type(node))
                if isinstance(node, xml.dom.minidom.Text):
                    continue
                print(node.childNodes[0].data)



aa = TestDemo()
aa.test_case1()