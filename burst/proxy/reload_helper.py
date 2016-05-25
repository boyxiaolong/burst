# -*- coding: utf-8 -*-

from collections import defaultdict


class ReloadHelper(object):

    STATUS_STOPPED = 0
    STATUS_PREPARING = 1      # 准备中
    STATUS_WORKERS_DONE = 2   # 已经准备好了

    proxy = None
    status = None

    # 预备役workers，使用dict，可以保证判断的时候更准确
    workers_dict = None

    def __init__(self, proxy):
        self.status = self.STATUS_STOPPED
        self.proxy = proxy
        self.workers_dict = defaultdict(set)

    def start(self):
        """
        启动
        :return:
        """
        self.status = self.STATUS_PREPARING

    def stop(self):
        """
        停止
        :return:
        """
        self.status = self.STATUS_STOPPED

    def add_worker(self, worker):
        """
        添加worker
        :param worker:
        :return:
        """
        self.workers_dict[worker.group_id].add(worker)

        for group_id, group_info in self.proxy.app.config['GROUP_CONFIG'].items():
            expect_count = group_info['count']

            if len(self.workers_dict[group_id]) != expect_count:
                # 只要找到一个没有满足的，就可以扔掉了
                return False
        else:
            self.status = self.STATUS_WORKERS_DONE
            return True

    @property
    def running(self):
        return self.status in (self.STATUS_PREPARING, self.STATUS_WORKERS_DONE)