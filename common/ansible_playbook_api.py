#!/usr/bin/python
# -*- coding: utf-8 -*-
import json
from ansible.parsing.dataloader import DataLoader
from ansible.vars import VariableManager
from ansible.inventory import Inventory
from ansible.executor.playbook_executor import PlaybookExecutor
from ansible.plugins.callback import CallbackBase
from common.redis_api import Rs
from common.ansible_api import ResultCallback


loader = DataLoader()  # 用来加载解析yaml文件或JSON内容,并且支持vault的解密
variable_manager = VariableManager()  # 管理变量的类,包括主机,组,扩展等变量,之前版本是在 inventory 中的
inventory = Inventory(loader=loader, variable_manager=variable_manager)
variable_manager.set_inventory(inventory)  # 根据 inventory 加载对应变量


class Options(object):
    '''
    这是一个公共的类,因为ad-hoc和playbook都需要一个options参数
    并且所需要拥有不同的属性,但是大部分属性都可以返回None或False
    因此用这样的一个类来省去初始化大一堆的空值的属性
    '''

    def __init__(self):
        self.connection = "ssh"
        self.forks = 1
        # self.ask_pass = "root"
        # self.ask_become_pass = "huo244"
        # self.verbose = "-vvv"
        self.check = False

    def __getattr__(self, name):
        return None


def api(tid, yml_list, extra_vars={}):
    print 'task id: {tid}'.format(tid=tid)
    print 'yml path: {yml}'.format(yml=yml_list)
    print 'extra_vars: {extra_vars}'.format(extra_vars=extra_vars)
    options = Options()
    results_callback = ResultCallback(tid)
    playbooks = yml_list  # 这里是一个列表, 因此可以运行多个playbook
    # variable_manager.extra_vars={"ansible_ssh_user":"root" , "ansible_ssh_pass":"root"}  # 增加外部变量
    variable_manager.extra_vars = extra_vars  # 增加外部变量
    pb = PlaybookExecutor(playbooks=playbooks, inventory=inventory, variable_manager=variable_manager, loader=loader,
                          options=options, passwords=None)
    pb._tqm._stdout_callback = results_callback
    result = pb.run()
    return result


if __name__ == '__main__':
    # yml_list = ['/Users/huozhihui/huo/ansible/user.yaml']
    tid = '1'
    yml_list = ['/etc/ansible/roles/nginx_install.yaml']
    yml_list = ['/Users/huozhihui/huo/ansible/roles/mysql_install/tasks/main.yaml']
    extra_vars = {
        # "ansible_ssh_user": "root",
        # "ansible_ssh_pass": "root",
        # "ip": '20.20.20.0'
        }
    api(tid, yml_list, extra_vars)