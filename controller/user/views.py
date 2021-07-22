"""
用户相关接口
"""
from flask import Blueprint, jsonify, g, render_template, request
from flask_restful import Api, Resource, marshal_with, reqparse, fields

from utils.appium_tool import get_user_ip
user = Blueprint('user', __name__, url_prefix='/user')
from exts import db

api = Api(user)
from utils import restful
from controller.project.models import AlterUser
import json


@user.route("/login", methods=['POST'])
def login():
    ip = get_user_ip(request)
    username = request.json["username"]
    password = request.json["password"]
    print("ip", ip)
    user = AlterUser.query.filter(AlterUser.username == username).first()

    resultData = {}
    if user and user.check_password(password):
        resultData["userId"] = user.id
        resultData["userName"] = user.username
        resultData["useDatas"] = user.useDatas

        return restful.success(data=resultData)
    else:
        user = AlterUser.query.filter(AlterUser.ip == ip).first()
        if user is not None:
            return restful.params_error(data={"userName": user.userName}, message="该电脑已经注册过一次")

        user = AlterUser(username=username, password=password, ip=ip)
        db.session.add(user)
        db.session.commit()
        resultData["userId"] = user.id
        resultData["userName"] = user.username
        resultData["useDatas"] = user.useDatas

        return restful.success(data=resultData)


@user.route("/getUser")
def get_user():
    userId = request.args.get('userId')
    resultData = {}
    if userId is not None:
        user = AlterUser.query.filter(AlterUser.id == userId).first()
        resultData["userId"] = user.id
        resultData["userName"] = user.username
        resultData["useDatas"] = user.useDatas
        return restful.success(data=resultData)
    else:
        users = AlterUser.query.all()
        resultDatas = []
        for user in users:
            resultDatas.append({
                "userId": user.id,
                "userName": user.username
            })
        return restful.success(data=resultDatas)


@user.route("/updateUser", methods=['POST'])
def update_user():
    parser = reqparse.RequestParser()
    parser.add_argument('useDatas', required=False, type=list)
    parser.add_argument('userId', required=True, type=int)
    parser.add_argument('password', required=False, type=str)
    args = parser.parse_args()

    useDatas = str(json.dumps(obj=args["useDatas"], ensure_ascii=False))
    userId = args["userId"]
    password = args["password"]
    userObj = AlterUser.query.filter(AlterUser.id == userId).first()

    if userObj is None:
        return restful.params_error("用户不存在")

    else:
        userObj.useDatas = useDatas
        if password is not None and password != "":
            userObj.password = password

        db.session.commit()
        return restful.success(message="修改成功", data=useDatas)
