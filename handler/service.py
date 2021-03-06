from tornado.web import HTTPError

from handler.base import BaseHandler
from orm.db import session_scope
from tasks.log_task import audit_log
from worker.run_task import run_celery_task

task_name_map = {
    'status': "查询应用状态",
    'start': "启动应用",
    'stop': '停止应用',
    'restart': "重启应用",
    "list": "列举该主机部署的应用"
}


class ServiceOperationHandler(BaseHandler):
    def get(self, *args, **kwargs):
        argus = self.url_arguments
        pattern_id = argus.pop('pattern_id', None)
        cmdstr = argus.pop('cmd', 'status')
        publish_host_ids = argus.pop('publish_host_ids', None)
        publish_host_id_list = publish_host_ids.split(',')

        if not publish_host_ids:
            raise HTTPError(status_code=400,
                            reason="Missing argument publish_host_ids ")
        task_name = task_name_map[cmdstr]
        with session_scope() as ss:
            host_and_id_list = run_celery_task(
                session=ss, publish_host_id_list=publish_host_id_list,
                task_name=task_name, pattern_id=pattern_id)

        for resource_id in publish_host_id_list:
            audit_log(self, description=task_name, resource_type=3, resource_id=resource_id)
        self.render_json_response(code=200, msg='OK', res=host_and_id_list)
