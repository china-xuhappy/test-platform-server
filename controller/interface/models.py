from exts import db

# class AlterDynamicVariable(db.Model):
#     """
#     动态变量
#     """
#     __tablename__ = "alter_dynamic_variable"
#     id = db.Column(db.Integer(), unique=False, primary_key=True, autoincrement=True)
#     paramsId = db.Column(db.Integer())
#     variableName = db.Column(db.String(255))
#     variableValue = db.Column(db.String(255))
#     remark = db.Column(db.String(255))
#     is_delete = db.Column(db.String(2))  # 1删除 0未删除
#
#     def __init__(self, paramsId, variableName, variableValue, remark, is_delete):
#         self.paramsId = paramsId
#         self.variableName = variableName
#         self.variableValue = variableValue
#         self.remark = remark
#         self.is_delete = is_delete
