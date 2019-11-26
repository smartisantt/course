# Create your tasks here
from __future__ import absolute_import, unicode_literals

from common.exceptions import QPSError
from parentscourse_server.celeryconfig import app

import logging

from common.textAPI import TextAudit
from client.models import Comments


@app.task(autoretry_for=(QPSError,), retry_kwargs={'max_retries': 5, 'countdown': 5})
def textWorker(uuid):
    """
    消费者处理任务
    :param uuid:
    :return:
    """
    text = TextAudit()
    comment = Comments.objects.filter(uuid=uuid).first()
    if comment:
        checkResult, checkInfo, = text.work_on(comment.content)
        if checkResult:
            if checkResult == 18:
                raise QPSError("QPS超限！！！")
            if checkResult in ["check", "checkFail", "checkAgain"]:
                checkDict = {
                    "check": 2,
                    "checkFail": 3,
                    "checkAgain": 4
                }
                comment.interfaceStatus = checkDict[checkResult]
                comment.interfaceInfo = checkInfo
                try:
                    comment.save()
                except Exception as e:
                    logging.error(str(e))
        return True


def get_task_status(task_id):
    task = textWorker.AsyncResult(task_id)

    status = task.state
    progress = 0

    if status == u'SUCCESS':
        progress = 100
    elif status == u'FAILURE':
        progress = 0
    elif status == 'PROGRESS':
        progress = task.info['progress']

    return {'status': status, 'progress': progress}
