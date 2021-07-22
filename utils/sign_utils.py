import hashlib


def get_md5(parmStr):
    if isinstance(parmStr, str):
        parmStr = parmStr.encode("utf-8")
    m = hashlib.md5()
    m.update(parmStr)
    return m.hexdigest()


def getStrAsMD5(origin):
    result = []
    s = ""
    for i in range(len(origin)):
        s += origin[i]
        if i % 2 != 0:
            int_hex = int(s, 16)
            result.append(int_hex)
            s = ""
    return result


def dec2hex(string_num):
    base = [str(x) for x in range(10)] + [chr(x) for x in range(ord('A'), ord('A') + 6)]

    num = int(string_num)
    mid = []
    while True:
        if num == 0: break
        num, rem = divmod(num, 16)
        mid.append(str(base[rem]).lower())

    return ''.join([str(x) for x in mid[::-1]])


not_list = ["true", "none", "None", "NULL"]


# "qGOSWGrd7wAXZhZHhP6fgR4kOUwr8Drz8crxqct1OgkBM1S7LeBPC0ukCX6v8S/dFpuJF7hpH73+cO3/9uiHbg=="
def getInterfaceSign1(params, sign):
    # del params["sign"]
    params_list = []
    for (k, v) in params.items():
        if isinstance(v, str) and k != "sign" and v not in not_list:
            params_list.append(str(k).upper())
            params_list.append(v)

    print(params_list)
    content = []
    print("".join(params_list).upper() + sign)
    print(getStrAsMD5(get_md5("".join(params_list).upper() + sign)))
    for i in getStrAsMD5(get_md5("".join(params_list).upper() + sign)):
        if i < 0:
            i += 256
        if i < 16:
            content.append("0")
        content.append(dec2hex(i))
    params["sign"] = "".join(content)
    print(params)
    return "".join(content)
