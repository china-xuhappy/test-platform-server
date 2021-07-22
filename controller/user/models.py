"""
和数据库 映射类
"""
from exts import db
from datetime import datetime


class SecondaryFile(db.Model):
    __tablename__ = "secondary_file"
    id = db.Column(db.Integer(), unique=False, primary_key=True, autoincrement=True)
    file_path = db.Column(db.String(255))
    type = db.Column(db.String(255)) #0支付文件, 1退款文件, 2确认收货文件
    file_name = db.Column(db.String(255))
    is_delete = db.Column(db.String(2))
    create_time = db.Column(db.DateTime)  # 创建时间

    __mapper_args__ = {
        "order_by": create_time.desc()
    }

    def __init__(self, file_path, type, file_name):
        self.file_path = file_path
        self.type = type
        self.file_name = file_name
        self.is_delete = 0
        self.create_time = datetime.now()
