"""
UI自动化 -- appium xml 解析
"""

import xml.dom.minidom
from pandas import Series

# 存储句子
data_list = []
# 存储句子标注极性
label_list = []

# if __name__ == '__main__':
#     # 获取xml文件
#     document_tree = xml.dom.minidom.parse("home.xml")
#     # 获取文件中的元素
#     collection = document_tree.documentElement
#     # 打印文件
#     # print(collection.toxml())
#     print(collection.nodeName)
#     print(collection.childNodes)
#     for i in collection.childNodes:
#         if isinstance(i, xml.dom.minidom.Text):
#             print("是文本")
#             continue
#         print(i)
#         print(type(i))
#         print(i.nodeName)
#         print(i.childNodes)
    # 获取xml文件中子标签内容
    # Doc_node = collection.getElementsByTagName("Doc")
    # for i in range(len(Doc_node)):
    #     sentence_node = Doc_node[i].getElementsByTagName("Sentence")
    #     for j in range(len(sentence_node)):
    #         # 剔除没有标注的数据
    #         if sentence_node[j].getAttribute("label") == "0" \
    #                 or sentence_node[j].getAttribute("label") == "1" \
    #                 or sentence_node[j].getAttribute("label") == "2":
    #             # 获取句子数据
    #             sentence = sentence_node[j].firstChild.data
    #             # 获取句子标注的极性
    #             label = sentence_node[j].getAttribute("label")
    #             data_list.append(sentence)
    #             label_list.append(label)
    # print(data_list[l]+"\t"+label_list[l])
    # print('\n')


elements = []

def parseAppiumXml(element):

    # print(a)
    # print(b)
    if isinstance(element, list):
        for i in element:
            try:
                if isinstance(i, xml.dom.minidom.Element):
                    # print("是文本")
                    # continue
                    parseAppiumXml(i)
            except Exception as e:
                pass

    elif isinstance(element, xml.dom.minidom.Element):
        clickable = element.getAttribute("clickable") #可点击
        enabled = element.getAttribute("enabled") #有效的
        checkable = element.getAttribute("checkable") #可用的
        text = element.getAttribute("text") #文本 控件名
        scrollable = element.getAttribute("scrollable") #可滚动
        selected = element.getAttribute("selected") #下拉 可选择的
        bounds = element.getAttribute("bounds") #范围 （坐标）
        displayed = element.getAttribute("displayed") #是否显示的
        resource_id = element.getAttribute("resource-id")  # id
        childNodes = element.childNodes
        # print("element： ", element.nodeName, "text: ", text, "clickable: ", clickable, "enabled: ", enabled, "bounds：", bounds)
        if clickable == "true" and enabled == "true":
            if text == "":
                #首页文字不支持点击 上级支持点击。 所以需要获取下级文本 进行初始化。
                for i in childNodes:
                    try:
                        if isinstance(i, xml.dom.minidom.Element):
                            text = i.getAttribute("text") #文本 控件名
                            if text != "":
                                break
                    except Exception as e:
                        pass
            # if text != "":
            bounds_first_index = bounds.find("]")
            bounds_first = bounds[:bounds_first_index + 1]
            bounds_last = bounds[bounds_first_index + 1:]
            print("text: ", text, "clickable: ", clickable,"resource_id: ", resource_id, "bounds_first：", bounds_first, "bounds_last: ", bounds_last)
            elements.append({
                "text": text,
                "clickable": 1 if clickable == "true" else 0,
                "resource_id": resource_id,
                "bound_first": str(tuple(eval(bounds_first))),
                "bound_last": str(tuple(eval(bounds_last))),
                "enabled": 1 if enabled == "true" else 0,
                "checkable": 1 if checkable == "true" else 0
            })

        if len(childNodes) != 0:
            parseAppiumXml(childNodes)

    else:
        isError = False

    return elements




# 获取xml文件
# document_tree = xml.dom.minidom.parse("aaa.xml")
# aa =document_tree.documentElement
# print(aa.childNodes[0].data)
# # 获取文件中的元素
# print(parseAppiumXml())
