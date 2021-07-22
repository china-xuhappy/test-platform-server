#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @File  : xmind_utils.py
# @Author: kaixin.xu
# @Date  : 2020/4/1
# @Desc  : xmind工具类，用来把xmind转Excel用例

from xmindparser import xmind_to_dict
import re,xlwt,os,config
import numpy as np
relust = []
lista = []
num1 = 0
num2 = 0

class xmind_utils():
    """
    合并的时候 获取要合并多少行， 有问题。。。
    """
    def get_merge_num(self,datas):
        global lista,num1,num2
        if isinstance(datas,list):
            for data in datas:
                self.get_merge_num(data)

        if isinstance(datas,dict):
            if "topics" in datas:
                topics = datas["topics"]
                # if len(topics) >= num1:
                lista.append(len(topics))

                if len(topics) > 1 and num2 == 0:
                    # self.num -=1
                    num2 += 1
                print(lista)
                lista = list(filter(lambda x: x != 1, lista))
                if len(lista) != 0:
                #     if 1 in lista:
                #         lista.remove(1)

                    num1 = max(lista)
                    self.num += num1

                lista = []
                self.get_merge_num(topics)
        return self.num

    def write_datas_excle(self,datas):
        global num1,num2
        if isinstance(datas,list):
            for data in datas:
                self.current_line += 1
                self.write_datas_excle(data)
                self.current_line -= 1

        if isinstance(datas,dict):
            if "topics" in datas:
                datas_copy = datas["topics"]
                title = datas["title"]

                self.num = 0
                num1 = 0
                num2 = 0
                self.row += self.get_merge_num(datas)
                if len(title) >= 20:
                    self.arise_width_list.append(self.current_line)

                if self.current_row >= 0:
                    r1 = self.current_row
                else:
                    r1 = 0

                # r2 = (self.row - 1) + self.current_row

                if r1 > 0:
                    r2 = r1

                self.sheet.write_merge(r1, r2, self.current_line, self.current_line, title, self.style)
                self.row = 0
                self.num = 0
                # self.current_row += 1
                return self.write_datas_excle(datas_copy)

            else:
                title = datas["title"]
                if len(title) >= 20:
                    self.arise_width_list.append(self.current_line)


                self.sheet.write(self.current_row, self.current_line, title, self.style)
                self.current_row += 1
            # self.current_row -= 1

    def write_excel(self,xmind_file,fileName=''):
        self.num = 0
        font = xlwt.Font()
        font.blod = True
        xlwt.Pattern()
        self.style = xlwt.XFStyle()
        self.style.font = font
        self.style.alignment.vert = 0x01
        self.style.alignment.horz = 0x02
        self.style.alignment.wrap = 1
        self.xls_name = fileName
        # self.style.font.height = 100
        # self.style.font.weight = 256*20
        self.current_row = 2
        self.row = 0

        self.line = 0
        self.current_line = 0

        self.br_line = 0
        self.f = xlwt.Workbook()
        self.sheet =self.f.add_sheet('测试用例',cell_overwrite_ok=True)


        self.arise_width_list = [] #记录出现宽度长的行
        self.row0 = ["用例Id", '功能模块', '测试步骤', '预期结果', '测试人员']
        for i in range(0,len(self.row0)):
            self.sheet.write(0,i,self.row0[i],self.style)

        self.out = xmind_to_dict(xmind_file)
        # self.xls_name = self.out[0]['topic']['title']
        self.story = self.out[0]['topic']['topics']
        self.storynum = len(self.story)

        # self.last_row = 0
        last_row = 0
        for index, value_dict in enumerate(self.story, 1):
            last_row = self.get_merge_num(value_dict)
            self.write_datas_excle(value_dict)
            self.line = 0
            self.current_line = 0
        unique_datas = np.unique(self.arise_width_list)
        for i in unique_datas:
            if self.arise_width_list.count(i) >= 1:
                self.sheet.col(int(i)).width = 256 * 20

            if self.arise_width_list.count(i) >= 5:
                self.sheet.col(int(i)).width = 256 * 50

        excle_url = os.path.join(config.UPLOAD_FOLDER, self.xls_name+ '.xls')

        self.f.save(excle_url)


