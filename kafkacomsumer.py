import os, django


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "parentscourse_server.settings")
django.setup()


from client.models import Chats
from logging.handlers import TimedRotatingFileHandler
import json
import logging
import kafka
from kafka import KafkaConsumer, KafkaAdminClient

from common.models import ChatsRoom
from parentscourse_server.config import KAFKA_HOST, KAFKA_CONSUMER_TOPIC, KAFKA_CONSUMER_GROUP, IM_PLATFORM


if __name__ == '__main__':

    consumer = KafkaConsumer(bootstrap_servers=KAFKA_HOST)
    print(consumer.topics())
    consumer.close()

    adminClient = KafkaAdminClient(bootstrap_servers=KAFKA_HOST, )
    # res = adminClient.delete_topics(KAFKA_CONSUMER_TOPIC)  # 删除topic

    # 校验消费者是否存在，如果不存在则新建
    if KAFKA_CONSUMER_TOPIC not in consumer.topics():
        topic = kafka.admin.NewTopic(name=KAFKA_CONSUMER_TOPIC, num_partitions=1, replication_factor=1)
        res = adminClient.create_topics([topic])            # 创建topic

    consumer = KafkaConsumer(KAFKA_CONSUMER_TOPIC, group_id=KAFKA_CONSUMER_GROUP, bootstrap_servers=KAFKA_HOST)
    try:
        for msg in consumer:

            if msg.value:
                try:
                    data = json.loads(msg.value.decode("utf-8"))
                    msgBodyString = json.loads(msg.value.decode("utf-8"))['MsgBody'][0]["MsgContent"]['Data']
                    msgBodyDict = json.loads(json.loads(msg.value.decode("utf-8"))['MsgBody'][0]["MsgContent"]['Data'])
                    if IM_PLATFORM == "TM":
                        chatroom = ChatsRoom.objects.filter(roomChapterUuid__status=1,
                                                            tmId=msgBodyDict.get("room_id")).first()
                    else:
                        chatroom = ChatsRoom.objects.filter(roomChapterUuid__status=1,
                                                            huanxingId=msgBodyDict.get("room_id")).first()

                    if Chats.objects.filter(msgSeq=data.get("MsgSeq"), roomUuid=chatroom).exists():
                        Chats.objects.filter(msgSeq=data.get("MsgSeq"), roomUuid=chatroom).\
                            update(msgTime=data.get("MsgTime") * 1000)
                    else:
                        if msgBodyDict.get("type") != "ppt-pos":
                            Chats.objects.create(
                                isQuestion=msgBodyDict.get("isQuestion", None),
                                roomUuid=chatroom,
                                talkType=msgBodyDict.get("type"),
                                userRole=msgBodyDict.get("role"),
                                content=msgBodyString,
                                displayPos=msgBodyDict.get("display"),
                                msgSeq=data.get("MsgSeq"),
                                msgTime=data.get("MsgTime") * 1000,
                                msgStatus=1,
                                duration=msgBodyDict.get("duration", None),
                                fromAccountUuid_id=msgBodyDict.get("from_uid", None)
                            )
                except Exception as e:
                    logging.error(str(e))

    except KeyboardInterrupt as e:
        logging.error(str(e))
