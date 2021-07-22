from gevent import monkey
monkey.patch_all()

from ui_controller.case import ui_case
from ui_controller.suite import ui_suite


from gevent.pywsgi import WSGIServer
from flask import Flask
from controller.user import user
from controller.project import project
from controller.common import common
from controller.case import case
from controller.interface import interface
from ui_controller.element import element
from controller.aotu import aotu
from controller.common import func
import config
from exts import db, scheduler, mongo
from utils.alter_log import handler


def create_app():
    app = Flask(__name__)
    app.config.from_object(config)
    app.register_blueprint(user)
    app.register_blueprint(project)
    app.register_blueprint(common)
    app.register_blueprint(func)
    app.register_blueprint(case)
    app.register_blueprint(aotu)
    app.register_blueprint(interface)
    app.register_blueprint(element)
    app.register_blueprint(ui_case)
    app.register_blueprint(ui_suite)

    db.init_app(app)
    mongo.init_app(app)
    scheduler.init_app(app)
    scheduler.start()
    app.logger.addHandler(handler)
    return app


app = create_app()

@app.route('/')
def hello_world():
    return 'Hello World!'.replace("\\\\", "/")


if __name__ == '__main__':
    from werkzeug.debug import DebuggedApplication

    app = DebuggedApplication(app, evalex=True)

    WSGIServer(("127.0.0.1", 5000), app).serve_forever()
    # app.run(host="127.0.0.1",debug=True,port=5000,threaded=True)

# x： 42
#
# y：102
#
# x - y：(30, 136)
# x - y：(105, 211)


"""
接口自动化测试数据

##车辆
#######    test2
carNO: 11
plateNum: 沪ZDH111
memNo: 111

##用户
mobile: 17601245833
memNo: 11111

#stuty
#APP性能
gt、
emmage


html 写代码控件
ace_editor


#获取apk信息
aapt dump badging E:\aotu.apk


adb shell dumpsys activity activities | findstr "Run"
"""