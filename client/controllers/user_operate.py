#!/usr/bin/python
# -*- coding: utf-8 -*-
from client.controllers import *
from client.forms import CreateUserForm


def index(request):
    title_name = _title_name()
    class_name = _class_name()
    init_date = {'remove': 'no', 'system': 'no'}
    form = CreateUserForm(initial=init_date)
    object_list = ext_helper.get_objects(request, 'Host')
    render_url = "%s/%s" % (_class_name(), 'index.html')
    return render(request, render_url, locals())


def get_result(request):
    if request.method == 'POST':  # 当提交表单时
        form = CreateUserForm(request.POST)  # form 包含提交的数据
        if form.is_valid():  # 如果提交的数据合法
            date = request.POST
            tid = ext_helper.generate_tid()
            _ansible_api(tid, date)
            # 将redis中的数据整理成对象列表
            redis_result = redis_api.RedisResult(tid)
            object_list = redis_result.get_instance()
            pattern = "{tid}*".format(tid=tid)
            for key in redis_api.Rs.scan_iter(match=pattern):
                redis_api.Rs.delete(key)
    else:
        error_msg = "Status 400: 错误的请求方式!"
    render_url = "base/_result.html"
    return render(request, render_url, locals())



def _ansible_api(tid, form_date):
    hosts = form_date['hosts']
    ext_vars = {"ansible_ssh_user": "root", "ansible_ssh_pass": "root"}
    params = {k: v for k, v in form_date.iteritems() if k not in ['hosts', 'csrfmiddlewaretoken']}
    if params['remove'] == 'yes':
        params['state'] = 'absent'
    ansible_api.api(tid, 'user', hosts, params, ext_vars)


def _title_name():
    return '用户操作'


def _class_name():
    return 'user_operate'