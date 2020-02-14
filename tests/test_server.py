"""Test flask app serving data from a Kafka stream."""

import datetime
import json
import time

from kafka import KafkaConsumer, KafkaProducer
import requests


TIMESTAMP_FORMAT = '%Y-%m-%d %H:%M:%S'


def test_compute_metrics(environment):
    """End to end test for /compute/metrics endpoint."""

    # consumer = KafkaConsumer('temperature', bootstrap_servers='localhost:9092',
    #     auto_offset_reset='earliest',
    #     value_deserializer=lambda x: int.from_bytes(x, byteorder='big'))
    # for msg in consumer:
    #    print(msg)

    _populate_kafka_topic('temperature')
    to_time = datetime.datetime.now()
    from_time = to_time - datetime.timedelta(minutes=1)
    body = {'temperature': ['count', 'min', 'max', 'average'],
            'from': from_time.strftime(TIMESTAMP_FORMAT),
            'to': to_time.strftime(TIMESTAMP_FORMAT)}
    print(body)
    # Build request with from: now - 1 min and to: now and all the metrics: check ==
    # Build ok request with a few unexpected key and check ==
    # Build a request with only unexpected shit and check it returns an error
    headers = {'Content-Type': 'application/json'}
    r = requests.post(url='http://localhost:5000/compute/metrics',
                      headers=headers, data=json.dumps(body))
    assert r.status_code == 200
    print(r.json())
    # assert len(r.json()["offers_ids"]) == len(body["offers"])
    # offers_order = [offer["id"] for offer in body["offers"]]
    # assert offers_order == r.json()["offers_ids"]


def _populate_kafka_topic(topic_name):
    """Send a few test values to the given kafka topic running locally."""
    producer = KafkaProducer(bootstrap_servers='localhost:9092')
    for value in range(10):
        producer.send(topic_name, bytes([value]))
        time.sleep(1)
