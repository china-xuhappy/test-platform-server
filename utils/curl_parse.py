#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @File  : curl_parse.py
# @Author: kaixin.xu
# @Date  : 2020/4/6
# @Desc  : 用来做解析的， copy curl格式，解析对应的数据

# url 解析成小块, http，host，等
import json


def url_parse(url):
    result = {}
    url = str(url)
    result["type"] = url[0: url.find(":")]  # http, https
    url_host = url[url.index("//") + 2:]
    result["host"] = url_host[0: url_host.index("/")]
    urlNew = url_host[url.index("/"):]
    result["route"] = urlNew[urlNew.index("/"):]

    return result


# get请求 参数转json
def getUrl_to_json(href):
    hrefs = href.split("?")
    params = hrefs[1]
    url = hrefs[0]

    paramArr = params.split('&')
    res = {}
    for param in paramArr:
        str1 = param.split('=')
        res[str1[0]] = str1[1]

    return url, res


def charles_to_json(param):
    param = param.strip().replace(" ", "").replace("\'", "\"").replace('\n', '').replace('\r', '')
    paramStrs = param.split("-H")
    result = {
        "method": "GET"
    }
    headers = {}
    for paramStr in paramStrs:
        if "curl" in paramStr:
            continue
        index = int(paramStr.find(":"))
        if "data-binary" in paramStr:
            datas = paramStr.split("--data-binary")
            result["method"] = "POST"
            print(datas[1].find("--compressed"))
            parameter = {}
            if "XPUT" in datas[1]: #PUT请求特殊获取
                parameter = datas[1][1:datas[1].find("-XPUT") - 1]
            else:
                parameter = datas[1][1:datas[1].find("--compressed") - 1]

            result["params"] = json.loads(parameter)
            paramStr = datas[1][datas[1].find("--compressed"):]

        if "compressed" in paramStr:
            urls = paramStr.split("--compressed")
            url = urls[1].replace("\"", "")
            paramStr = urls[0]
            key = paramStr[1: index]
            value = paramStr[index + 1: -1]
            headers[key] = value

            if result["method"] == "POST":
                result["url"] = url
                result["urlLong"] = url

            else:
                result["urlLong"] = url
                result["params"] = getUrl_to_json(url)[1]
                result["url"] = getUrl_to_json(url)[0]
        else:
            key = paramStr[1: index]
            value = paramStr[index + 1: -1]
            headers[key] = value

    result.update(url_parse(result["url"]))
    result["headers"] = headers

    return result


"""
转浏览器copy的 curl
"""


def browser_to_json(param):
    result = {
        "method": "GET"
    }
    headers = {}
    param = param.strip().replace(" ", "").replace("\'", "\"").replace('\n', '').replace('\r', '').replace('\\', '')
    param = param[:param.find("--compressed")]
    if "data-binary" in param:
        result["method"] = "POST"

    paramStrs = param.split("-H")

    for paramStr in paramStrs:
        index = int(paramStr.find(":"))
        if "data-binary" in paramStr:
            datas = paramStr.split("--data-binary")
            data = datas[1][1:-1]
            print(data)
            result["params"] = json.loads(data)
            paramStr = datas[0]

        if "curl" in paramStr:
            urls = paramStr.split("curl")
            url = urls[1].replace("\"", "")
            if result["method"] == "POST":
                result["url"] = url
                result["urlLong"] = url

            else:
                result["urlLong"] = url
                result["params"] = getUrl_to_json(url)[1]
                result["url"] = getUrl_to_json(url)[0]
        else:
            key = paramStr[1: index]
            value = paramStr[index + 1: -1]
            headers[key] = value

    result.update(url_parse(result["url"]))
    result["headers"] = headers

    return result


# browser_curl = '''
# curl 'https://www.atzuche.com/apigateway/dictionaryService/public/car/param/list/children?token=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJqYmsiOiJ7XCJsb2dpbklkXCI6XCIzODc1XCIsXCJsb2dpbk5hbWVcIjpcIuWGr-S-neaWh1wiLFwibG9naW5UaW1lXCI6MTU4Njk1MTYyMDg0OSxcImlzQWRtaW5cIjoxfSJ9.AHP5UstG87_6227tAHUT6sXWyvFrJchDKjr9Hd1wZ5o&requestId=1587006945305'
# -H 'Connection: keep-alive'
# -H 'Accept: application/json;version=3.0;compress=false'
# -H 'Sec-Fetch-Dest: empty'
# -H 'Authorization: eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJqYmsiOiJ7XCJsb2dpbklkXCI6XCIzODc1XCIsXCJsb2dpbk5hbWVcIjpcIuWGr-S-neaWh1wiLFwibG9naW5UaW1lXCI6MTU4Njk1MTYyMDg0OSxcImlzQWRtaW5cIjoxfSJ9.AHP5UstG87_6227tAHUT6sXWyvFrJchDKjr9Hd1wZ5o'
# -H 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.163 Safari/537.36'
# -H 'Content-Type: application/json;charset=utf-8' -H 'Sec-Fetch-Site: same-origin' -H 'Sec-Fetch-Mode: cors'
# -H 'Referer: https://www.atzuche.com/system/transaction/order/ordinary/detail/orderInfo/11782151400299' -H 'Accept-Language: zh-CN,zh;q=0.9'
# -H 'Cookie: gr_user_id=19c9d35c-459e-418a-9cec-e04c6251ae02;grwng_uid=20f66586-ef8d-4006-9acc-8cf5aa958018; 946c38810f0edb65_gr_last_sent_cs1=385151127; 946c38810f0edb65_gr_cs1=385151127; Hm_lvt_940ac302dc9436169f5e98f17aca1589=1586242620,1586326273,1586399520,1586777353; Hm_lpvt_940ac302dc9436169f5e98f17aca1589=1586951705' --compressed
# '''
if __name__ == '__main__':
    charles_curl = '''
        curl 
        -H 'User-Agent: Autoyol_113:Android_22|43AB5EB5CD5257E431D1772FA71CF2EED3D33E0E04F4E33D33E7EBEB23' 
        -H 'Accept: application/json;version=3.0;compress=false' 
        -H 'X-Tingyun-Id: YfYbInNBhKA;c=2;r=2025925503;u=a959b261c42426e756118205816b44bf::423DF79271B79FDD' 
        -H 'Content-Type: application/json; charset=utf-8' 
        -H 'Host: test2-appserver.atzc.com:7065' 
        --data-binary '{"OsVersion":"22","source":"1","token":"bb138bbcbd6f4421a478cf595beec3bc","useBal":"0","itemList":[{"itemKey":"abatementFlag","itemValue":"0"}],"srvGetAddr":"黄浦路60号海鸥饭店2层","srvReturnFlag":"1","schema":"B","IMEI":"863254010020070","srvReturnAddr":"黄浦路60号海鸥饭店2层","sceneCode":"EX005","oilType":"3","OAID":"","publicToken":"bb138bbcbd6f4421a478cf595beec3bc","AppVersion":113,"PublicLongitude":"0","deviceName":"MI6","rentCity":"上海","srvReturnLat":"31.243801","PublicLatitude":"0","srvGetLat":"31.243801","requestId":"02004C4F4F501586853463341","freeDoubleTypeId":"3","androidID":"02004c4f4f503831","mac":"02004C4F4F50","shuntFlagStr":"1","srvReturnLon":"121.49162","srvGetLon":"121.49162","OS":"ANDROID","mem_no":"643164996","AppChannelId":"testmarket","appName":"atzucheApp","publicCityCode":"021","cityCode":"310100","revertTime":"20200513210000","carNo":"207670092","srvGetFlag":"1","rentTime":"20200512090000","AndroidId":"02004c4f4f503831","queryId":null,"isLeaveCity":"0","useAirportService":"0","conPhone":"16940000000","limitRedStatus":"0","useAutoCoin":"0"}' 
        --compressed 'https://test2-appserver.atzc.com:7065/v61/newOrder/req'
        '''
    charles_to_json(charles_curl)

    # browser_curl = '''
    # curl
    # 'https://www.atzuche.com/apigateway/orderAdmin/console/order/cancel/judgeDuty/list'
    # -H 'Connection: keep-alive'
    # -H 'Accept: application/json;version=3.0;compress=false'
    # -H 'Sec-Fetch-Dest: empty'
    # -H 'Authorization: eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJqYmsiOiJ7XCJsb2dpbklkXCI6XCIzODc1XCIsXCJsb2dpbk5hbWVcIjpcIuWGr-S-neaWh1wiLFwibG9naW5UaW1lXCI6MTU4Njk1MTYyMDg0OSxcImlzQWRtaW5cIjoxfSJ9.AHP5UstG87_6227tAHUT6sXWyvFrJchDKjr9Hd1wZ5o'
    # -H 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.163 Safari/537.36'
    # -H 'Content-Type: application/json;charset=UTF-8' -H 'Origin: https://www.atzuche.com' -H 'Sec-Fetch-Site: same-origin'
    # -H 'Sec-Fetch-Mode: cors'
    # -H 'Referer: https://www.atzuche.com/system/transaction/order/ordinary/detail/orderInfo/11782151400299'
    # -H 'Accept-Language: zh-CN,zh;q=0.9'
    # -H 'Cookie: gr_user_id=19c9d35c-459e-418a-9cec-e04c6251ae02; grwng_uid=20f66586-ef8d-4006-9acc-8cf5aa958018; 946c38810f0edb65_gr_last_sent_cs1=385151127; 946c38810f0edb65_gr_cs1=385151127; Hm_lvt_940ac302dc9436169f5e98f17aca1589=1586242620,1586326273,1586399520,1586777353; Hm_lpvt_940ac302dc9436169f5e98f17aca1589=1586951705'
    # --data-binary '{"orderNo":"11782151400299","pageSize":10,"pageNum":1,"token":"eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJqYmsiOiJ7XCJsb2dpbklkXCI6XCIzODc1XCIsXCJsb2dpbk5hbWVcIjpcIuWGr-S-neaWh1wiLFwibG9naW5UaW1lXCI6MTU4Njk1MTYyMDg0OSxcImlzQWRtaW5cIjoxfSJ9.AHP5UstG87_6227tAHUT6sXWyvFrJchDKjr9Hd1wZ5o","requestId":1587006945320}' --compressed
    # '''
    #
    # print(str(browser_to_json(browser_curl)).replace("\'", "\""))
