#!/usr/bin/python
# -*- coding: utf-8 -*-
from django.db import transaction
from workflow.controllers import *
from workflow.models import Task, TaskLog, HomeWork, RoleManage, Task_Result
import threading

L = threading.Lock()  # 引入锁


def index(request):
    title_name = _title_name()
    class_name = _class_name()
    msg = ext_helper.get_msg(request)
    object_list = ext_helper.get_objects(request, 'TaskLog')
    render_url = "%s/%s" % (_class_name(), 'index.html')
    return render_to_response(render_url, locals())


def select(request, id):
    id = ext_helper.to_int(id)
    class_name = _class_name()
    task = Task.objects.get(pk=id)
    homework = task.homework
    title_name = homework.name
    msg = ext_helper.get_msg(request)
    object_list = task.tasklog_set.all()
    render_url = "%s/%s" % (_class_name(), 'select.html')
    return render_to_response(render_url, locals())


def delete(request, id):
    id = ext_helper.to_int(id)
    obj = TaskLog.objects.get(pk=id)
    obj.delete()
    if obj.id:
        request.session['msg'] = "数据删除失败!"
    else:
        request.session['msg'] = "数据删除成功!"
    return index(request)


def ws_get_deploy_result(ws, task_log_id, ip):
    task_log_id = ext_helper.to_int(task_log_id)
    redis_key_info = "{tid}-{ip}-info".format(tid=task_log_id, ip=ip)
    redis_key_result = "{tid}-{ip}-result".format(tid=task_log_id, ip=ip)
    # 一、调用"待部署"方法,即调用ansible接口,如果异常发送"部署异常"的状态
    # 二、生成线程,轮询状态(status),
    #       1、如果"部署失败"则退出循环并发送数据;
    #       2、如果"正在部署"则调用"正在部署"的方法;
    status = _status(redis_key_info)
    if status == 0:
        try:
            _set_deploy(ws, redis_key_info)
        except Exception, e:
            print e
            redis_api.Rs.hmset(redis_key_info, {'status': 4, 'status_name': "部署失败"})
            _send_data(ws, redis_key_info, 'server_error')

    # 生成线程,获取ansible返回结果并发回前端
    _get_ansible_result(ws, task_log_id, redis_key_info, redis_key_result)


# @ext_helper.thread_method
def _get_ansible_result(ws, task_log_id, r_key_info, r_key_result):
    while True:
        status = _status(r_key_info)
        if status > 2:
            break
        if status == 2:
            redis_api.Rs.delete(r_key_info)
            print "清除{r_key_info}的redis缓存".format(r_key_info=r_key_info)
            break
        if status == 1:
            try:
                _get_deploy_result(ws, r_key_info, r_key_result)
            except Exception, e:
                print e
                redis_api.Rs.hmset(r_key_info, {'status': 4, 'status_name': "部署失败"})
                _send_data(ws, r_key_info, 'server_error')


# @ext_helper.thread_method
# def main(ws, task_log_id, r_key_info, redis_key_result, status):
#     try:
#         # 状态-待部署
#         if status == 0:
#             _set_deploy(ws, r_key_info)
#
#         # 状态-正在部署
#         if status == 1:
#             _get_deploy_result(ws, r_key_info, redis_key_result)
#     except Exception, e:
#         print e
#         redis_api.Rs.hmset(r_key_info, {'status': 4, 'status_name': "部署失败"})
#         _send_data(ws, r_key_info, 'server_error')


# 发送ws数据方法
@ext_helper.thread_method
def _send_data(ws, r_key_info, ws_status='success'):
    try:
        ws_status_dict = {
            'success': 'websocket访问服务端正常。',
            'deploy_error': '{host_ip}部署失败,请重试成功后继续完成部署。'.format(host_ip=_host_ip(r_key_info)),
            'server_error': '部署{host_ip}时,服务端异常,请解决异常后继续完成部署。'.format(host_ip=_host_ip(r_key_info))
        }
        ws_msg = ws_status_dict[ws_status]
        progress_per = _progress_per(r_key_info)
        progress_num = _progress_num(r_key_info)
        send_data = {
            'id': _task_log_id(r_key_info),
            'status': _status(r_key_info),
            'status_name': _status_name(r_key_info),
            'use_time': _use_time(r_key_info),
            'progress_per': progress_per,
            'progress_num': progress_num,
            'ws_status': ws_status,
            'ws_msg': ws_msg
        }
        ws.send(text=json.dumps(send_data), bytes=None)
    except Exception, e:
        print 'Warn: {r_key_info} send data exception.'.format(r_key_info=r_key_info)
        print e


# 待部署的状态
@ext_helper.thread_method
def _set_deploy(ws, r_key_info):
    tid = _task_log_id(r_key_info)
    host_ip = _host_ip(r_key_info)
    params_json = _params(r_key_info)
    role_name = _role_name(r_key_info)
    playbook = _playbook(r_key_info)
    playbook_name = _playbook_name(r_key_info)
    # 如果事pre_install 角色,切换ubuntu用户
    params = json.loads(params_json)

    # 首先发送"正在部署"的状态
    redis_api.Rs.hmset(r_key_info, {'status': 1, 'status_name': "正在部署"})
    _send_data(ws, r_key_info)

    content = []
    msg = '开始安装部署{playbook_name}......'.format(playbook_name=playbook_name)
    content.append(msg)
    print '主机{host_ip}{msg}'.format(host_ip=host_ip, msg=msg)

    # 生成yml文件
    print "主机{host_ip}开始生成yml文件".format(host_ip=host_ip)
    new_yml = _create_ip_yml(host_ip, playbook)
    if not new_yml:
        redis_api.Rs.hmset(r_key_info, {'status': 3, 'status_name': "部署失败"})
        msg = '生成yml文件失败。'
        content.append(msg)
        _save_set_deploy(tid, content, r_key_info)
        _send_data(ws, r_key_info, ws_status='deploy_error')
        return False

    # 统计yml文件中任务步骤
    print "主机{host_ip}开始统计yml文件中步骤数".format(host_ip=host_ip)
    step_count = _yml_step_count(host_ip, new_yml)
    if step_count:
        redis_api.Rs.hmset(r_key_info, {'step_count': step_count})
    else:
        redis_api.Rs.hmset(r_key_info, {'status': 3, 'status_name': "部署失败"})
        msg = '计算yml文件步骤失败。'
        content.append(msg)
        _save_set_deploy(tid, content, r_key_info)
        _send_data(ws, r_key_info, ws_status='deploy_error')
        return False

    os.system('ssh-keygen -R {host_ip}'.format(host_ip=host_ip))
    resule_code = _playbook_api(tid, new_yml, params, host_ip, role_name)
    if resule_code:
        redis_api.Rs.hmset(r_key_info, {'status': 1, 'status_name': "正在部署"})
        msg = '调用{playbook_name} playbook成功!'.format(playbook_name=playbook_name)
        content.append(msg)
        print '主机{host_ip}{msg}'.format(host_ip=host_ip, msg=msg)

        msg = '正在获取{playbook_name} playbook运行结果......'.format(playbook_name=playbook_name)
        content.append(msg)
        print '主机{host_ip}{msg}'.format(host_ip=host_ip, msg=msg)
        ws_status = 'success'
    else:
        redis_api.Rs.hmset(r_key_info, {'status': 3, 'status_name': "部署失败"})
        msg = '调用{playbook_name} playbook失败'.format(playbook_name=playbook_name)
        content.append(msg)
        print '主机{host_ip}{msg}'.format(host_ip=host_ip, msg=msg)
        ws_status = 'deploy_error'
    _save_set_deploy(tid, content, r_key_info)
    _send_data(ws, r_key_info, ws_status)



# 保存开始部署后接口调用的信息数据
def _save_set_deploy(tid, content, r_key_info):
    if content:
        content_str = ','.join(content)
        redis_api.Rs.hset(r_key_info, 'content', content_str)
        data = {
            'status': _status(r_key_info),
            'timeout': _use_time(r_key_info),
            'step_count': _step_count(r_key_info),
            'begin_deploy_at': datetime.now(),
            'content': content_str,
        }
        # 保存结果数据
        TaskLog.objects.filter(id=tid).update(**data)


# @ext_helper.thread_method
def _get_deploy_result(ws, r_key_info, r_key_result):
    tid = _task_log_id(r_key_info)
    host_ip = _host_ip(r_key_info)
    playbook_name = _playbook_name(r_key_info)
    timeout = _timeout(r_key_info)
    use_time = _use_time(r_key_info)
    step_count = _step_count(r_key_info)
    current_step = _current_step(r_key_info)
    content = _content(r_key_info).split(',')
    ws_status = 'success'

    print "{now}正在获取ansible的返回结果。".format(now=datetime.now())
    if use_time >= timeout:
        redis_api.Rs.hmset(r_key_info, {'status': 3, 'status_name': "部署失败"})
        msg = '{playbook_name} playbook运行超时!'.format(playbook_name=playbook_name)
        content.append(msg)
        ws_status = 'deploy_error'
        _send_data(ws, r_key_info, 'deploy_error')
        _save_set_deploy(tid, content, r_key_info)
        print '主机{host_ip}部署{msg}'.format(host_ip=host_ip, msg=msg)
    else:
        # 获取结果
        rs_result = redis_api.Rs.lrange(r_key_result, 0, -1)
        if rs_result:
            rs_data = rs_result[0]
            result = json.loads(rs_data)
            ansible_status = result.get('ansible_status', None)
            # 如果部署完成
            if step_count == (current_step + 1):
                if ansible_status in ['ok', 'changed', 'skipped']:
                    redis_api.Rs.hmset(r_key_info, {'status': 2, 'status_name': "部署成功"})
                    msg = '{playbook_name}部署成功。'.format(playbook_name=playbook_name)
                    content.append(msg)
                    print '主机{host_ip}部署任务结束, {playbook_name}部署成功。'.format(host_ip=host_ip, playbook_name=playbook_name)
                else:
                    redis_api.Rs.hmset(r_key_info, {'status': 3, 'status_name': "部署失败"})
                    msg = '{playbook_name}部署失败。'.format(playbook_name=playbook_name)
                    content.append(msg)
                    ws_status = 'deploy_error'
                    print '主机{host_ip}部署任务结束, {playbook_name}部署失败。'.format(
                        host_ip=host_ip,
                        playbook_name=playbook_name
                    )
            else:
                if ansible_status not in ['ok', 'changed', 'skipped']:
                    redis_api.Rs.hmset(r_key_info, {'status': 3, 'status_name': "部署失败"})
                    msg = '{playbook_name}部署失败。'.format(playbook_name=playbook_name)
                    content.append(msg)
                    ws_status = 'deploy_error'
                    print '主机{host_ip}部署任务结束, {playbook_name}部署失败。'.format(host_ip=host_ip,
                                                                           playbook_name=playbook_name)

            # 保存ansible返回的结果
            try:
                Task_Result.objects.create(**result)
                redis_api.Rs.hincrby(r_key_info, 'current_step', 1)
                print "主机{host_ip}存储ansible结果成功。".format(host_ip=host_ip)
            except Exception, e:
                redis_api.Rs.hmset(r_key_info, {'status': 3, 'status_name': "部署失败"})
                msg = "主机{host_ip}存储ansible结果异常。".format(host_ip=host_ip)
                content.append(msg)
                ws_status = 'deploy_error'
                print msg
                print e
            else:
                redis_api.Rs.lpop(r_key_result)
            # 当部署成功、失败时保存状态
            _save_set_deploy(tid, content, r_key_info)
            _send_data(ws, r_key_info, ws_status)
        redis_api.Rs.hincrby(r_key_info, 'use_time', 2)
        time.sleep(2)



def _save_get_deploy_result(tid, content, r_key_info):
    if content:
        content_str = ','.join(content)
        redis_api.Rs.hset(r_key_info, 'content', content_str)
        data = {
            'status': _status(r_key_info),
            'timeout': _use_time(r_key_info),
            'content': content_str,
        }
        # 保存结果数据
        TaskLog.objects.filter(id=tid).update(**data)


# 根据ip生成对应的yml文件
def _create_ip_yml(host_ip, playbook):
    try:
        yaml_path = os.path.join(settings.ANSIBLE_YAMLS, playbook)
        with open(yaml_path, 'r+') as f:
            config, ind, bsi = load_yaml_guess_indent(f)
            config[0]['hosts'] = str(host_ip)

        yml_name = str(host_ip).replace('.', '_')
        new_yml = "{name}.yml".format(name=yml_name)
        tmp_ansible_yml = os.path.join(settings.ANSIBLE_YAMLS, new_yml)
        with open(tmp_ansible_yml, 'w') as f:
            ruamel.yaml.round_trip_dump(config, f, indent=ind, block_seq_indent=bsi)
        return tmp_ansible_yml
    except Exception, e:
        print '主机{host_ip}生成yml文件失败,{error_msg}'.format(host_ip=host_ip, error_msg=e)
        return None


# 统计yml文件中任务步骤
def _yml_step_count(host_ip, yml_path):
    try:
        with open(yml_path, 'r+') as f:
            data = yaml.load(f)
            roles = data[0].get('roles', None)
            step_count = 0
            if roles:
                for role in roles:
                    role_yaml_path = os.path.join(settings.ANSIBLE_YAMLS, 'roles', role, 'tasks/main.yml')
                    with open(role_yaml_path, 'r+') as rf:
                        for d in yaml.load(rf):
                            if d.get('name', None):
                                step_count += 1
            else:
                tasks = data[0].get('tasks', None)
                for d in tasks:
                    if d.get('name', None):
                        step_count += 1
        return step_count
    except Exception, e:
        print '主机{host_ip}生成yml文件失败,{error_msg}'.format(host_ip=host_ip, error_msg=e)
        return None


# 调用playbook_api 接口
# @ext_helper.thread_method
def _playbook_api(tid, yml_path, params, host_ip, role_name):
    try:
        yaml_list = [str(yml_path)]
        # 将params插入到额外变量
        extra_vars = params
        if role_name == 'pre_install':
            host_list = os.path.join(settings.ANSIBLE_HOSTS, 'pre_install_hosts')
            code = ansible_playbook_api.api(tid, host_list, yaml_list, extra_vars)
        else:
            host_list = os.path.join(settings.ANSIBLE_HOSTS, 'hosts')
            code = ansible_playbook_api.api(tid, host_list, yaml_list, extra_vars)
        if os.path.exists(yml_path):
            os.remove(yml_path)

            # retry_yml = "{name}.retry".format(name=yml_name)
            # tmp_retry_yml = os.path.join(settings.ANSIBLE_YAMLS, retry_yml)
            # if os.path.exists(tmp_ansible_yml):
            #     os.remove(tmp_ansible_yml)
        return True
    except Exception, e:
        print '主机{host_ip}调用playbook接口失败, {error_msg}'.format(host_ip=host_ip, error_msg=e)
        return False


def _task_log_id(r_key_info):
    return int(_get_redis_value(r_key_info, 'id'))


def _params(r_key_info):
    return _get_redis_value(r_key_info, 'params')


def _role_name(r_key_info):
    return _get_redis_value(r_key_info, 'role_name')


def _playbook(r_key_info):
    return _get_redis_value(r_key_info, 'playbook')


def _playbook_name(r_key_info):
    return _get_redis_value(r_key_info, 'playbook_name')


def _host_ip(r_key_info):
    return _get_redis_value(r_key_info, 'host_ip')


def _current_step(r_key_info):
    return int(_get_redis_value(r_key_info, 'current_step'))


def _step_count(r_key_info):
    return int(_get_redis_value(r_key_info, 'step_count'))


def _status(r_key_info):
    return int(_get_redis_value(r_key_info, 'status'))


def _status_name(r_key_info):
    return _get_redis_value(r_key_info, 'status_name')


def _timeout(r_key_info):
    return int(_get_redis_value(r_key_info, 'timeout'))


def _use_time(r_key_info):
    return int(_get_redis_value(r_key_info, 'use_time'))


def _content(r_key_info):
    return _get_redis_value(r_key_info, 'content')


def _progress_per(r_key_info):
    try:
        current_step = _current_step(r_key_info)
        step_count = _step_count(r_key_info)
        per = current_step * 100 / float(step_count)
        return "{0:.0f}%".format(per)
    except Exception, e:
        return "0%"


def _progress_num(r_key_info):
    current_step = _current_step(r_key_info)
    step_count = _step_count(r_key_info)
    return '{0}/{1}'.format(current_step, step_count)


# 重新部署
@transaction.atomic
def retry_deploy(request, id):
    id = ext_helper.to_int(id)
    tid = request.session.get('tid')
    task_logs = TaskLog.objects.filter(pk=id)
    task_log = task_logs[0]
    request.session['tid'] = task_log.task_id
    try:
        # 事务处理
        task_logs.update(
            content="",
            status=0,
            ansible_status="",
            begin_deploy_at=datetime.now(),
            timeout=task_log.role_manage.timeout
        )
        Task.objects.filter(id=tid).update(status=1)
        task_log.task_result_set.all().delete()
        # 重试清除
        redis_api.Rs.delete(task_log.redis_key_result())
        redis_api.Rs.hmset(task_log.redis_key_info(), {
            'status': 0,
            'status_name': "待部署",
            'use_time': 0,
            'current_step': 0,
            'content': ''})
        msg = "success"
    except Exception, e:
        print e
        msg = "error"
    return HttpResponse(json.dumps({'msg': msg, 'status_name': "待部署"}),
                        content_type='application/json')


# 实时更新剩余时间
def update_rest_time(request, key):
    # 当redis缓存先被清除后, 则停止前端时间刷新
    # if not redis_api.Rs.hexists(key):
    #     state = 'stop'
    #     msg = ''
    #     return HttpResponse(json.dumps({'state': state, 'msg': msg}), content_type='application/json')
    # else:
    try:
        redis_api.Rs.hincrby(key, 'use_time')
        timeout = redis_api.Rs.hget(key, 'timeout')
        use_time = redis_api.Rs.hget(key, 'use_time')
        real_time = int(timeout) - int(use_time)
        if real_time < 0:
            real_time = 0
        state = "success"
        msg = time.strftime('%H:%M:%S', time.gmtime(real_time))
    except Exception, e:
        msg = "{key}的剩余时间更新异常, 请处理异常后继续完成部署。".format(key=key)
        print msg
        print e.message
        state = "error"

    return HttpResponse(json.dumps({'state': state, 'msg': msg}), content_type='application/json')


def _get_redis_value(key, field):
    try:
        return redis_api.Rs.hget(key, field)
    except Exception, e:
        return None


def _deploy_failed(r_key_info, error_msg):
    redis_api.Rs.hmset(r_key_info, {'status': 3, 'status_name': "部署失败"})
    print error_msg
    return False


def _title_name():
    return '部署明细'


def _class_name():
    return 'task_log'
