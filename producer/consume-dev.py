"""Consume data from a kafka topic, only here for testing purpose."""

from datetime import datetime
import os

from kafka import KafkaConsumer, TopicPartition

TIMESTAMP_FORMAT = '%Y-%m-%d %H:%M:%S'

if __name__ == '__main__':

    kafka_socket = os.environ['KAFKA_SOCKET']
    kafka_topic = os.environ['KAFKA_TOPIC']

    # consumer = KafkaConsumer(kafka_topic, bootstrap_servers=kafka_socket, auto_offset_reset='earliest',
    #                          value_deserializer=lambda x: int.from_bytes(x, byteorder='big'))
    consumer = KafkaConsumer(kafka_topic, bootstrap_servers=kafka_socket,
                             value_deserializer=lambda x: int.from_bytes(x, byteorder='big'))

    ts1 = "2020-01-12 13:56:00"
    ts2 = "2020-01-12 14:10:00"
    from_tstamp = datetime.strptime(ts1, TIMESTAMP_FORMAT)
    to_tstamp = datetime.strptime(ts2, TIMESTAMP_FORMAT)

    k_from = int(round(from_tstamp.timestamp() * 1000))
    k_to = int(round(to_tstamp.timestamp() * 1000))
    offset_from = consumer.offsets_for_times({TopicPartition(kafka_topic, 0): k_from})
    offset_to = consumer.offsets_for_times({TopicPartition(kafka_topic, 0): k_to})
    print(offset_from, offset_to)

    # for msg in consumer:
    #     log.info(msg)
