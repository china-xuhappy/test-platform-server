"""

获取apk信息，
包名，启动项，版本 等信息
"""
import math
import platform
from math import floor
import subprocess
import os


def get_systemsta():
    """根据所运行的系统获取adb不一样的筛选条件"""
    system = platform.system()
    if system == 'Windows':
        find_manage = 'findstr'
    else:
        find_manage = 'grep'
    return find_manage


find_manage = get_systemsta()


class ApkInfo():
    def __init__(self, apkpath):
        self.apkpath = apkpath

    # 得到app的文件大小
    def get_apk_size(self):
        size = floor(os.path.getsize(self.apkpath) / (1024 * 1000))
        return str(size) + "M"

    # 得到版本
    def get_apk_version(self):
        cmd = "aapt dump badging " + self.apkpath + " | {find_manage} versionName".format(find_manage=find_manage)
        result = ""
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE,
                             stdin=subprocess.PIPE, shell=True)
        (output, err) = p.communicate()
        if output != "":
            result = output.split()[3].decode()[12:]
        return result

    # 得到应用名字
    def get_apk_name(self):
        cmd = "aapt dump badging " + self.apkpath + " | {find_manage} application-label: ".format(
            find_manage=find_manage)
        result = ""
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE,
                             stdin=subprocess.PIPE, shell=True)
        (output, err) = p.communicate()
        if output != "":
            result = output.split()[0].decode()[18:]
        return result

    # 得到包名
    def get_apk_pkg(self):
        cmd = "aapt dump badging " + self.apkpath + " | {find_manage} package:".format(find_manage=find_manage)
        result = ""
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE,
                             stdin=subprocess.PIPE, shell=True)
        (output, err) = p.communicate()
        if output != "":
            result = output.split()[1].decode()[6:-1]
        return result

    # 得到启动类
    def get_apk_activity(self):
        cmd = "aapt dump badging " + self.apkpath + " | {find_manage} launchable-activity:".format(
            find_manage=find_manage)
        result = ""
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE,
                             stdin=subprocess.PIPE, shell=True)
        (output, err) = p.communicate()
        if output != "":
            result = output.split()[1].decode()[6:-1]
        return result


def get_phone_info(devices):
    """

        获取设备的一些基本信息
    """
    cmd = "adb -s " + devices + " shell cat /system/build.prop "
    phone_info = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout.readlines()
    release = "ro.build.version.release="  # 版本
    model = "ro.product.model="  # 型号
    brand = "ro.product.brand="  # 品牌
    device = "ro.product.device="  # 设备名
    result = {"release": release, "model": model, "brand": brand, "device": device}
    for line in phone_info:
        for i in line.split():
            temp = i.decode()
            if temp.find(release) >= 0:
                result["release"] = temp[len(release):]
                break
            if temp.find(model) >= 0:
                result["model"] = temp[len(model):]
                break
            if temp.find(brand) >= 0:
                result["brand"] = temp[len(brand):]
                break
            if temp.find(device) >= 0:
                result["device"] = temp[len(device):]
                break
    return result


# 得到最大运行内存
def get_men(devices):
    cmd = "adb -s " + devices + " shell cat /proc/meminfo"
    get_cmd = os.popen(cmd).readlines()
    men_total = 0
    men_total_str = "MemTotal"
    for line in get_cmd:
        if line.find(men_total_str) >= 0:
            men_total = line[len(men_total_str) + 1:].replace("kB", "").strip()
            break
    return int(men_total)


# 得到几核cpu
def get_cpu(devices):
    cmd = "adb -s " + devices + " shell cat /proc/cpuinfo"
    get_cmd = os.popen(cmd).readlines()
    find_str = "processor"
    int_cpu = 0
    for line in get_cmd:
        if line.find(find_str) >= 0:
            int_cpu += 1
    return str(int_cpu) + "核"


# 得到手机分辨率
def get_pix(devices):
    result = os.popen("adb -s " + devices + " shell wm size", "r")
    return result.readline().split("Physical size:")[1]


if __name__ == '__main__':
    print(ApkInfo(r"E:\aotu.apk").get_apk_pkg())
    print(ApkInfo(r"E:\aotu.apk").get_apk_version())
    print(ApkInfo(r"E:\aotu.apk").get_apk_name())
    print(ApkInfo(r"E:\aotu.apk").get_apk_activity())
    print(get_phone_info("emulator-5554"))
    print(get_men("emulator-5554"))
    print(get_cpu("emulator-5554"))
    print(get_pix("emulator-5554"))
