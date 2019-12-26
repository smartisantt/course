
import time

from kafka import KafkaProducer
from kafka.errors import KafkaError

from parentscourse_server.config import KAFKA_HOST, KAFKA_CONSUMER_TOPIC

producer = KafkaProducer(bootstrap_servers=KAFKA_HOST)


def test():
    print('begin')
    n = 1
    try:
        while (n <= 10):
            producer.send(KAFKA_CONSUMER_TOPIC, "测试".encode()+str(n).encode())
            print("send" + str(n))
            n += 1
            time.sleep(0.5)
    except KafkaError as e:
        print(e)
    finally:
        producer.close()
        print('done')


if __name__ == '__main__':
    test()
