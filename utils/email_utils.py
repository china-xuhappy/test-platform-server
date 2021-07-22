"""
DESCRIPTION：邮件发送

:Created by Null.
"""
import smtplib
from os import path
from email.header import Header
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from os import path


class SendMail(object):

    def __init__(self):
        #, "yichao.xiong@atzuche.com"
        #
        self.receiver = ["kaixin.xu@atzuche.com", "han.xiao@atzuche.com", "yichao.xiong@atzuche.com", "lli@atzuche.com"]  # 发送人
        self.sendaddr_name = "kaixin.xu@atzuche.com"
        self.sendaddr_pswd = "At@zuche888"
        self.template = path.join(path.dirname(path.abspath(__file__)), 'templates/email')
        self.content = open(self.template, encoding='utf-8')
        self.con = self.content.read()

    def email_content(self, content: str):
        mail_body = self.con.format(content["amount"], content["success_num"], content["error_num"],content["reportUrl"])
        self.msg.attach(MIMEText(mail_body, _subtype='html', _charset='utf-8'))

    def send_mail(self, content: str):
        self.msg = MIMEMultipart()

        self.email_content(content)  # 发送报告
        self.msg['From'] = self.sendaddr_name
        self.msg['To'] = ','.join(self.receiver)
        self.msg['Subject'] = Header('《凹凸-接口自动化测试报告》', 'utf-8')
        server = smtplib.SMTP_SSL('smtp.qiye.163.com', 465)
        try:
            server.login(self.sendaddr_name, self.sendaddr_pswd)
            server.sendmail(self.sendaddr_name, self.receiver, self.msg.as_string())
        except smtplib.SMTPException as error:
            print(error)
        finally:
            server.quit()

# mail = SendMail()
# mail.send_mail({
#             "reportUrl": "http://10.0.3.246/#/reportDetail/{caseId}".format(caseId=111),
#             "success_num": 1,
#             "error_num": 2,
#             "amount": 3
#         })
