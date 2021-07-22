#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @File  : ap_sheduler.py
# @Author: kaixin.xu
# @Date  : 2020/4/4
# @Desc  : 定时任务接口
from exts import scheduler
from croniter import croniter
from datetime import datetime
from controller.project.models import AlterTasks
from exts import db

class APScheduler(object):
    """调度器控制方法"""
    def add_job(self, jobid, func, args, cron_dict,**kwargs):
        """
        添加任务
        :param args:  元祖 -> （1，2）
        :param jobstore:  存储位置
        """
        job_def = dict(kwargs)
        job_def['id'] = jobid
        job_def['func'] = func
        job_def['args'] = args
        job_def = self.fix_job_def(job_def,cron_dict)
        self.remove_job(jobid)  # 删除原job
        scheduler.add_job(**job_def)

    def remove_job(self, jobid, jobstore=None):
        """删除任务"""
        if scheduler.get_job(jobid) is not None:
            scheduler.remove_job(jobid, jobstore=jobstore)

    def resume_job(self, jobid, jobstore=None):
        """继续工作"""
        scheduler.resume_job(jobid, jobstore=jobstore)

    def pause_job(self, jobid, jobstore=None):
        """暂停工作"""
        scheduler.pause_job(jobid, jobstore=jobstore)

    def fix_job_def(self, job_def, cron_dict):
        """维修job工程"""
        if job_def.get('trigger') == 'date':
            job_def['run_date'] = job_def.get('run_date') or None
        elif job_def.get('trigger') == 'cron':
            job_def['second'] = cron_dict.get('second') or "*"
            job_def['minute'] = cron_dict.get('minute') or "*"
            job_def['hour'] = cron_dict.get('hour') or "*"
            job_def['day'] = cron_dict.get('day') or "*"
            job_def['month'] = cron_dict.get('month') or "*"
            job_def['year'] = cron_dict.get('year') or "*"
        elif job_def.get('trigger') == 'interval':
            job_def['seconds'] = job_def.get('seconds') or "*"
        return job_def

    def get_next_execute_time(self, params):
        """获取下一次执行时间"""
        try:
            self.crontab = params.get("crontab")
        except Exception as e:
            print(repr(e))
            return False, str(e)
        return True, str(croniter(self.crontab, datetime.now()).get_next(datetime))
