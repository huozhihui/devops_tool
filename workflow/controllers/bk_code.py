#!/usr/bin/python
# -*- coding: utf-8 -*-


# 部署前检查参数、节点和Redis
# def before_deploy_check(request):
#     msg = 'success'
#     tid = request.session['tid']
#     nodes = _get_nodes(tid)
#     if not nodes:
#         msg = "请至少配置一个节点后再部署。"
#
#     try:
#         redis_api.Rs.ping()
#     except Exception, e:
#         msg = "Redis连接失败, 请启动后再尝试。"
#     return HttpResponse(json.dumps({'msg': msg}), content_type='application/json')

# 查询任务的执行状态
# def get_deploy_result(request, id):
#     id = ext_helper.to_int(id)
#     task_log = TaskLog.objects.get(id=id)
#     task = Task.objects.get(id=task_log.task_id)
#     date = {'status': task_log.status,
#             'status_name': task_log.status_name()}
#
#     # 待部署的状态
#     if task_log.status == 0:
#         # 调用ansible playbook接口
#         begin_deploy(request, task_log)
#         TaskLog.objects.filter(id=id).update(status=1)
#         date = {'status': 1,
#                 'status_name': '正在部署'}
#
#     # 正在部署的状态
#     if task_log.status == 1:
#         key = '{tid}-{ip}'.format(tid=task.id, ip=task_log.host.ip)
#         rs_date = redis_api.Rs.hgetall(key)
#         ansible_status = rs_date.get('status', None)
#         rs_stderr = rs_date.get('stderr', None)
#         rs_stdout = rs_date.get('stdout', None)
#         content = rs_stderr or rs_stdout
#         if ansible_status:
#             if ansible_status in ['ok', 'changed']:
#                 date_status = 2
#                 date_status_name = '部署成功'
#             else:
#                 date_status = 3
#                 date_status_name = '部署失败'
#             TaskLog.objects.filter(id=id).update(status=date_status,
#                                                  ansible_status=ansible_status,
#                                                  content=content)
#             date = {'status': date_status,
#                     'status_name': date_status_name}
#
#     return HttpResponse(json.dumps(date), content_type='application/json')


# 开始部署
# @check_hid
# def begin_deploy(request, task_log):
#     print '开始部署{ip}'.format(ip=task_log.host.ip)
#     hid = request.session['hid']
#     tid = request.session['tid']
#     homework = HomeWork.objects.get(id=hid)
#     parameters = homework.parameter_set.filter(Q(user_id=request.user.id) | Q(user__is_superuser=1))
#     params_dict = dict(parameters.values_list('name', 'value'))
#
#     try:
#         role_manage = RoleManage.objects.get(name=task_log.role_name)
#     except Exception, e:
#         print '获取角色错误。'
#         return
#
#     playbook = role_manage.playbook
#     yaml_path = os.path.join(settings.ANSIBLE_ROLES, playbook, 'tasks', 'main.yaml')
#     yaml_list = [str(yaml_path)]
#
#     # 将params插入到额外变量
#     extra_vars = {}
#     extra_vars.update(params_dict)
#     try:
#         # code = ansible_playbook_api.api(tid, yaml_list, extra_vars)
#         print '调用Ansible PlayBook成功!'
#     except Exception, e:
#         print '调用Ansible PlayBook失败!'
#         print e

        # if code != 0:
        #     print '执行Ansible PlayBook脚本失败!'

# @ext_helper.thread_method
# def _get_deploy_result(task, task_log, data):
#     playbook_name = task_log.role_manage.playbook_name()
#     content = "正在获取{playbook_name} playbook运行结果......".format(playbook_name=playbook_name)
#     if task_log.timeout == 0:
#         if task_log.timeout == 0:
#             data.update({'status': 3, 'status_name': u"部署失败"})
#             content = '{playbook_name} playbook运行超时!'.format(playbook_name=playbook_name)
#             print '主机{host_ip}部署{content}'.format(host_ip=task_log.host.ip, content=content)
#     # else:
#     #     data.update({'status': 3, 'status_name': u"部署失败"})
#     #     content = '运行{playbook_name} playbook时开始时间为空,不能判断运行是否超时!'.format(playbook_name=playbook_name)
#     #     print '主机{host_ip}{content}'.format(host_ip=task_log.host.ip, content=content)
#
#     key = '{tid}-{ip}'.format(tid=task.id, ip=task_log.host.ip)
#     rs_date = redis_api.Rs.hgetall(key)
#     ansible_status = rs_date.get('status', None)
#     if ansible_status:
#         if ansible_status in ['ok', 'changed']:
#             data.update({'status': 2, 'status_name': u"部署成功"})
#             # date_status = 2
#             # date_status_name = '部署成功'
#             content = rs_date.get('stdout', None)
#         else:
#             data.update({'status': 3, 'status_name': u"部署失败"})
#             # date_status = 3
#             # date_status_name = '部署失败'
#             content = rs_date.get('stderr', None)
#
#         # 清除redis缓存
#         redis_api.Rs.delete(key)
#     TaskLog.objects.filter(id=task_log.id).update(status=data['status'],
#                                                   ansible_status=ansible_status,
#                                                   content=content)


# # 调用playbook_api 接口
# @ext_helper.thread_method
# def _playbook_api(tid, host, params, playbook):
#     # 生成hosts文件
#     tmp_host_dir = '/tmp/ansible_host_files'
#     file_path = os.path.join(tmp_host_dir, str(host.ip).replace('.', '_'))
#     if not os.path.exists(tmp_host_dir):
#         os.mkdir(tmp_host_dir)
#     playbook_name = playbook.split('.')[0]
#     with open(file_path, 'w') as f:
#         f.write('[%s]' % playbook_name)
#         f.write('\n')
#         content = "{ip} ansible_ssh_user={user} ansible_ssh_pass={password} ansible_ssh_port={port}".format(
#             ip=host.ip, user=host.username, password=host.password, port=host.port)
#         f.write(content)
#         f.write('\n')
#
#     # 将params插入到额外变量
#     extra_vars = params
#     yaml_path = os.path.join(settings.ANSIBLE_YAMLS, playbook)
#     yaml_list = [str(yaml_path)]
#     code = ansible_playbook_api.api(tid, file_path, yaml_list, extra_vars)
#     # os.remove(file_path)
