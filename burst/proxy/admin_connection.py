# -*- coding: utf-8 -*-

from twisted.internet.protocol import Protocol, Factory
from netkit.box import Box
import json

from ..utils import safe_call
from ..log import logger
from .. import constants


class AdminConnectionFactory(Factory):

    def __init__(self, proxy):
        self.proxy = proxy

    def buildProtocol(self, addr):
        return AdminConnection(self, addr)


class AdminConnection(Protocol):
    _read_buffer = None

    # 客户端IP的数字
    _client_ip_num = None

    def __init__(self, factory, address):
        self.factory = factory
        self.address = address
        self._read_buffer = ''

    def dataReceived(self, data):
        """
        当数据接受到时
        :param data:
        :return:
        """
        self._read_buffer += data

        while self._read_buffer:
            # 因为box后面还是要用的
            box = Box()
            ret = box.unpack(self._read_buffer)
            if ret == 0:
                # 说明要继续收
                return
            elif ret > 0:
                # 收好了
                self._read_buffer = self._read_buffer[ret:]
                safe_call(self._on_read_complete, box)
                continue
            else:
                # 数据已经混乱了，全部丢弃
                logger.error('buffer invalid. ret: %d, read_buffer: %r', ret, self._read_buffer)
                self._read_buffer = ''
                return

    def _auth_user(self, username, password):
        """
        验证用户
        :param username:
        :param password:
        :return:
        """

        return (self.factory.proxy.app.admin_username or '', self.factory.proxy.app.admin_password or '') == (
            username or '', password or ''
        )

    def _on_read_complete(self, box):
        """
        完整数据接收完成
        :param box: 解析之后的box
        :return:
        """

        # 无论是哪一种请求，都先验证用户
        req_body = json.loads(box.body)

        rsp = None

        if not self._auth_user(req_body['auth']['username'], req_body['auth']['password']):
            rsp = box.map(dict(
                ret=constants.RET_ADIMN_AUTH_FAIL
            ))
        else:
            if box.cmd == constants.CMD_ADMIN_SERVER_STAT:
                idle_workers = len(self.factory.proxy.job_dispatcher.idle_workers_dict)
                busy_workers = len(self.factory.proxy.job_dispatcher.busy_workers_dict)

                # 正在处理的
                pending_jobs_queue = self.factory.proxy.job_dispatcher.group_queue.queue_dict
                pending_jobs = dict([(group_id, queue.qsize()) for group_id, queue in pending_jobs_queue.items()])

                rsp_body = dict(
                    clients=self.factory.proxy.stat_counter.clients,
                    client_req=self.factory.proxy.stat_counter.client_req,
                    client_rsp=self.factory.proxy.stat_counter.client_rsp,
                    worker_req=self.factory.proxy.stat_counter.worker_req,
                    worker_rsp=self.factory.proxy.stat_counter.worker_rsp,
                    workers=dict(
                        all=idle_workers + busy_workers,
                        idle=idle_workers,
                        busy=busy_workers,
                    ),
                    pending_jobs=pending_jobs,
                    job_times=dict(self.factory.proxy.stat_counter.jobs_time_counter),
                )

                rsp = box.map(dict(
                    body=json.dumps(rsp_body)
                ))

        if rsp:
            self.transport.write(rsp.pack())

