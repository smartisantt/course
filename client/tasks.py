# Create your tasks here
from __future__ import absolute_import, unicode_literals

from django.db.models import F

from common.models import Orders, Bill, User
from parentscourse_server.celeryconfig import app

import logging

from utils.clientExceptions import QPSError
from utils.textAPI import TextAudit
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


@app.task
def checkPayWorker(uuid):
    """
    核对用户是否退款
    :param uuid:
    :return:
    """
    order = Orders.objects.filter(uuid=uuid).first()
    if order:
        if order.shareUserUuid and order.orderDetailUuid.first().goodsUuid.rewardStatus:
            status = order.payStatus
            if status == 2:

                money = order.shareMoney
                shareUser = order.shareUserUuid
                try:
                    Bill.objects.create(
                        userUuid=shareUser,
                        billType=1,
                        remarks="分销收入",
                        money=money
                    )
                    User.objects.filter(uuid=shareUser.uuid).update(income=F("income") + money,
                                                                    banlance=F("banlance") + money, isClasser=True)
                    order.shareMoneyStatus = 3
                    order.save()
                except Exception as e:
                    logging.error(str(e))
            elif status == 4:
                try:
                    order.shareMoneyStatus = 4
                    order.save()
                except Exception as e:
                    logging.error(str(e))
    return True


@app.task
def checkOrder(uuid):
    """
    如果半小时后未支付，则订单超时
    :param uuid:
    :return:
    """
    order = Orders.objects.filter(uuid=uuid).first()
    if order and order.payStatus == 1:
        order.payStatus = 5
        try:
            order.save()
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


if __name__ == "__main__":
    from datetime import datetime, timedelta

    checkPayWorker.apply_async(("ce8feeaf488e45f7b2feabf7919096e7",), eta=datetime.utcnow() + timedelta(seconds=10))
