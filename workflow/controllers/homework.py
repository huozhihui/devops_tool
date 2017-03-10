#!/usr/bin/python
# -*- coding: utf-8 -*-
from workflow.forms import HomeWorkForm, ParameterForm
from workflow.models import *
from workflow.controllers import *


# 检查hid是否存在的适配器
def check_hid(func):
    functools.wraps(func)

    def wrapper(*args, **kwargs):
        hid = args[0].session.get('hid', None)
        if hid:
            return func(*args, **kwargs)
        else:
            return HttpResponseRedirect('/homework')

    return wrapper


def index(request):
    title_name = _title_name()
    class_name = _class_name()
    msg = ext_helper.get_msg(request)
    object_list = ext_helper.get_objects(request, 'HomeWork')
    render_url = "%s/%s" % (_class_name(), 'index.html')
    return render_to_response(render_url, locals())


def new(request):
    title_name = _title_name()
    class_name = _class_name()
    operation = "添加"
    if request.method == 'POST':  # 当提交表单时
        form = HomeWorkForm(request.POST)  # form 包含提交的数据
        if form.is_valid():  # 如果提交的数据合法
            form.cleaned_data['user_id'] = request.user.id
            dates = form.cleaned_data
            obj = HomeWork.objects.create(**dates)
            obj.save()
            if obj.id:
                msg = u"%s 添加成功!" % dates['name']
            else:
                msg = u"%s 添加失败!" % dates['name']
    form = HomeWorkForm()
    return render(request, 'homework/form.html', locals())


def edit(request, id):
    id = ext_helper.to_int(id)
    title_name = _title_name()
    class_name = _class_name()
    operation = "编辑"
    # host_roles = RoleManage.objects.all()
    if request.method == 'POST':  # 当提交表单时
        form = HomeWorkForm(request.POST)  # form 包含提交的数据
        if form.is_valid():  # 如果提交的数据合法
            form.cleaned_data['user_id'] = request.user.id
            dates = form.cleaned_data
            if HomeWork.objects.filter(pk=id).update(**dates):
                msg = u"%s 编辑成功!" % dates['name']
                return index(request)
            else:
                msg = u"%s 编辑失败!" % dates['name']
                return render(request, 'homework/form.html', locals())
    else:
        host = HomeWork.objects.get(pk=id)
        form = HomeWorkForm(instance=host)
        return render(request, 'homework/form.html', locals())


def delete(request, id):
    id = ext_helper.to_int(id)
    obj = HomeWork.objects.get(pk=id)
    obj.delete()
    if obj.id:
        request.session['msg'] = "数据删除失败!"
    else:
        request.session['msg'] = "数据删除成功!"
    return index(request)


# *************************************** 选择部署 ********************************************
# 选择部署
def select_deploy(request, id):
    id = ext_helper.to_int(id)
    hid = request.session.get('hid', None)
    tid = request.session.get('tid', None)
    # 切换作业
    if id != hid:
        request.session['hid'] = id
        tid = None
    if tid:
        try:
            task = Task.objects.get(id=tid)
        except:
            task = None

        if (task and task.homework_id == id):
            request.session['msg'] = u"您还有未完成的部署任务(%s),请首先完成。" % task.uuid
            return HttpResponseRedirect("/task")
        else:
            _create_task(request, id, tid)
            # return HttpResponseRedirect("/homework/select_node")
            return HttpResponseRedirect("/homework/select_role")

    else:
        _create_task(request, id, tid)
        # return HttpResponseRedirect("/homework/select_node")
        return HttpResponseRedirect("/homework/select_role")


# *************************************** 选择角色 ********************************************
# 选择角色
@check_hid
def select_role(request):
    request.session['tab_active'] = 1
    hid = request.session.get('hid', None)
    homework = HomeWork.objects.get(id=hid)

    tid = request.session.get('tid', None)
    task_logs = TaskLog.objects.filter(task_id=tid, user_id=request.user.id)
    select_roles = [t.role_manage_id for t in task_logs]

    form_url = "/%s/confirm_role" % _class_name()
    object_list = ext_helper.get_objects(request, 'RoleManage')
    render_url = "%s/%s" % (_class_name(), 'select_role.html')
    return render(request, render_url, locals())


# 确认角色
def confirm_role(request):
    roles = map(int, request.POST.getlist('role'))
    hid = request.session.get('hid', None)
    tid = request.session.get('tid', None)
    user_id = request.user.id
    role_ids = TaskLog.objects.filter(task_id=tid).values_list('role_manage_id', flat=True)
    del_roles = list(set(role_ids).difference(set(roles)))

    # 删除所有的动态参数
    Parameter.objects.filter(user_id=user_id, homework_id=hid, is_dynamic_var=1).delete()

    # 删除取消的节点
    if del_roles:
        TaskLog.objects.filter(user_id=user_id, task_id=tid, role_manage_id__in=del_roles).delete()

    if roles:
        for role_id in roles:
            role_manage = RoleManage.objects.get(pk=role_id)
            host_ids = role_manage.host_role_set.all().values_list('host_id', flat=True)
            for host_id in list(host_ids):
                TaskLog.objects.get_or_create(task_id=tid,
                                              host_id=host_id,
                                              role_manage_id=role_id,
                                              user_id=user_id,
                                              status=0,
                                              timeout=role_manage.timeout
                                              )
                host_ip = Host.objects.get(pk=host_id).ip
                if role_manage.dynamic_vars:
                    dynamic_var_list = role_manage.dynamic_vars.split(',')
                    for var in dynamic_var_list:
                        d = {'homework_id': hid, 'role_manage_id': role_id, 'name': var, 'value': host_ip,
                             'user_id': user_id, 'is_dynamic_var': True}
                        Parameter.objects.get_or_create(**d)

    return config_params(request)


# *************************************** 选择节点 ********************************************
# 选择节点
def select_node(request):
    id = request.session['hid']
    request.session['tab_active'] = 1
    tab_name = "选择节点"

    tid = request.session.get('tid', None)
    task_logs = TaskLog.objects.filter(task_id=tid, user_id=request.user.id)
    select_nodes = [t.host_id for t in task_logs]

    form_url = "/%s/confirm_node" % _class_name()
    object_list = ext_helper.get_objects(request, 'Host')
    render_url = "%s/%s" % (_class_name(), 'select_node.html')
    return render(request, render_url, locals())


# 确认节点
def confirm_node(request):
    nodes = request.POST.getlist('node')
    tid = request.session.get('tid')
    user_id = request.user.id
    node_list = TaskLog.objects.filter(task_id=tid).values_list('host_id', flat=True)
    del_ids = list(set(node_list).difference(set(nodes)))
    # 删除取消的节点
    if del_ids:
        TaskLog.objects.filter(task_id=tid, host_id__in=del_ids).delete()
    if nodes:
        for nid in nodes:
            task_log = TaskLog.objects.get_or_create(task_id=tid, host_id=int(nid), user_id=user_id, status=0)
    # else:
    #     TaskLog.objects.filter(task_id=tid).delete()
    return config_params(request)


# *************************************** 参数 ********************************************
# 配置参数
@check_hid
def config_params(request):
    class_name = _class_name()
    msg = ext_helper.get_msg(request)
    request.session['tab_active'] = 2
    hid = request.session.get('hid', None)
    homework = HomeWork.objects.get(id=hid)

    tid = request.session.get('tid', None)
    role_manages = Task.objects.get(id=tid).role_manages

    parameters = homework.parameter_set.filter(Q(user_id=request.user.id) | Q(user__is_superuser=1))
    form = ParameterForm()
    form_url = "/%s/create_params" % _class_name()
    render_url = "%s/%s" % (_class_name(), 'config_params.html')
    return render(request, render_url, locals())


# 添加参数
def create_params(request):
    if request.method == 'POST':  # 当提交表单时
        d = {'homework_id': request.session['hid'], 'role_manage_id': request.POST['role_id']}
        instance, msg = ext_helper.create_date(request, 'Parameter', 'name', d)
        request.session['msg'] = msg
    return config_params(request)


# 编辑并提交参数
def update_params(request, id):
    dialog_title = "编辑参数"
    id = ext_helper.to_int(id)

    tid = request.session.get('tid', None)
    role_manages = Task.objects.get(id=tid).role_manages
    parameter = Parameter.objects.get(id=id)
    if request.method == 'GET':
        form = ParameterForm(instance=parameter)
        form_url = "/%s/update_params/%s" % (_class_name(), id)
        render_url = "%s/%s" % (_class_name(), 'config_params/dialog_edit.html')
        return render(request, render_url, locals())
    else:
        d = {'homework_id': request.session['hid'], 'role_manage_id': request.POST['role_id']}
        result_status, msg = ext_helper.update_date(request, id, 'Parameter', 'name', d)
        request.session['msg'] = msg
        return HttpResponseRedirect(request.POST['come_from'])


def delete_params(request, id):
    msg = ext_helper.delete_date(request, 'Parameter', id)
    return HttpResponse(json.dumps({'msg': msg}), content_type='application/json')


# *************************************** 确认部署 ********************************************
# 确认部署页面,删除某一节点
def delete_task_log(request, id):
    msg = ext_helper.delete_date(request, 'TaskLog', id)
    return HttpResponse(json.dumps({'msg': msg}), content_type='application/json')


# 确认部署
@check_hid
def confirm_deploy(request):
    class_name = _class_name()
    msg = ext_helper.get_msg(request)
    request.session['tab_active'] = 3
    hid = request.session['hid']
    tid = request.session['tid']

    homework = HomeWork.objects.get(id=hid)
    task = Task.objects.get(id=tid)
    parameters = homework.parameter_set.filter(Q(user_id=request.user.id) | Q(user__is_superuser=1))
    task_logs = task.tasklog_set.all()
    # nodes = _get_nodes(tid)

    render_url = "%s/%s" % (_class_name(), 'confirm_deploy.html')
    return render(request, render_url, locals())


# 部署进度
@check_hid
def deploy_status(request):
    hid = request.session['hid']
    tid = request.session['tid']
    base_url = ext_helper.base_url(request)
    homework = HomeWork.objects.get(id=hid)
    parameters = homework.parameter_set.filter(Q(user_id=request.user.id) | Q(user__is_superuser=1))
    params_dict = dict(parameters.values_list('name', 'value'))
    params_json = json.dumps(params_dict)
    task = Task.objects.get(id=tid)
    task_logs = task.tasklog_set.all()

    render_error_url = "%s/%s" % (_class_name(), 'confirm_deploy.html')
    # 判断任务角色是否存在
    if not task.role_manages():
        msg = "请至少选择一个角色后再部署。"
        return render(request, render_error_url, locals())
    else:
        # 判断任务角色对应的main.yaml文件是否存在
        for role_manage in task.role_manages():
            playbook = role_manage.playbook

            # yaml_path = os.path.join(settings.ANSIBLE_ROLES, playbook_name, 'tasks', 'main.yaml')
            yaml_path = os.path.join(settings.ANSIBLE_YAMLS, playbook)
            if not os.path.exists(yaml_path):
                msg = "{role_name}角色的playbook不存在: {path}。".format(
                    role_name=role_manage.name, path=yaml_path
                )
                print "%s文件不存在。" % str(yaml_path)
                return render(request, render_error_url, locals())

    if not task_logs:
        msg = "选择的角色至少关联一个节点后再部署。"
        return render(request, render_error_url, locals())

    # 生成ansible hosts文件
    hosts_path = os.path.join(settings.ANSIBLE, 'hosts')
    bk_path = os.path.join(settings.ANSIBLE, 'bk_hosts')
    try:
        _generate_ansible_hosts(hosts_path, bk_path, task_logs)
    except Exception, e:
        msg = "生成Ansible hosts文件失败, %s" % e
        return render(request, render_error_url, locals())

    try:
        redis_api.Rs.ping()
    except Exception, e:
        msg = "Redis连接失败, 请启动后再尝试。"
        return render(request, render_error_url, locals())

    # 更新task中的状态为开始部署(status)和参数(params)
    update_task = {'status': 1}
    if task.params != params_json:
        update_task['params'] = params_json
    Task.objects.filter(id=tid).update(**update_task)

    request.session['tab_active'] = 4
    deploy_list = task.tasklog_set.filter(Q(status=0) | Q(status=1))
    result_list = task.tasklog_set.filter(status__gte=2)
    render_url = "%s/%s" % (_class_name(), 'deploy_status.html')
    return render(request, render_url, locals())


def deploy_log(request, id):
    id = ext_helper.to_int(id)
    task_log = TaskLog.objects.get(id=id)
    dialog_title = '日志'
    render_url = "%s/%s" % (_class_name(), 'dialog_deploy_log.html')
    return render(request, render_url, locals())


def _get_nodes(tid):
    host_ids = [int(tl.host_id) for tl in TaskLog.objects.filter(task_id=tid)]
    return Host.objects.filter(id__in=host_ids)


def _create_task(request, hid, tid):
    homework = HomeWork.objects.get(id=hid)
    parameters = homework.parameter_set.filter(Q(user_id=request.user.id) | Q(user__is_superuser=1))
    params_dict = dict(parameters.values_list('name', 'value'))
    params_json = json.dumps(params_dict)
    task_list = Task.objects.filter(Q(id=tid) | Q(homework_id=hid, user_id=request.user.id, status=0))
    if task_list:
        task = task_list[0]
        if task.params != params_json:
            task_list.update(params=params_json)
    else:
        uuid = datetime.now().strftime("%Y%m%d%H%M%S")
        task = Task.objects.create(user_id=request.user.id,
                                   homework_id=hid,
                                   params=params_json,
                                   uuid=uuid,
                                   status=0)

    request.session['tid'] = task.id


def _generate_ansible_hosts(file_path, bk_path, task_logs):
    data = defaultdict(list)
    for task_log in task_logs:
        node = task_log.host
        d = OrderedDict()
        d['ip'] = node.ip
        d['username'] = node.username
        d['password'] = node.password
        d['port'] = node.port
        group_name = task_log.role_manage.playbook_name()
        data[group_name].append(d)

    if os.path.exists(file_path):
        shutil.move(file_path, bk_path)

    with open(file_path, 'w') as f:
        for group, value_list in data.items():
            f.write('[%s]' % group)
            f.write('\n')
            for v in value_list:
                content = "{ip} ansible_ssh_user={user} ansible_ssh_pass={password} ansible_ssh_port={port}".format(
                    ip=v['ip'], user=v['username'], password=v['password'], port=v['port'])
                f.write(content)
                f.write('\n')
            f.write('\n')


def _title_name():
    return '作业'


def _class_name():
    return 'homework'