"""Pytest fixtures."""

import os
import time

from kafka import KafkaProducer, KafkaAdminClient
import pytest


@pytest.yield_fixture(scope="session")
def environment():
    """Setup all the tests environment and tear it down after tests have run."""

    # Setup: start zookeper, kafka, flask server and populate the 'test' kafka topic
    os.system('nohup zookeeper-server-start /usr/local/etc/kafka/zookeeper.properties > /dev/null 2>&1 &')
    time.sleep(2)
    os.system('nohup kafka-server-start /usr/local/etc/kafka/server.properties > /dev/null 2>&1 &')
    time.sleep(2)
    print('zookepper and kafka started')
    # Would be much cleaner to:
        # create a package out of the consumer/ folder
        # define a functiong get_flask_app() in server.py to pass the flask app
        # start (and then stop) the flask app here from the python code
    # But no time for that now
    os.system('. .venv/bin/activate; nohup python consumer/server.py > serverlogs 2>&1 &')
    print('server started')
    time.sleep(2)
    # _populate_kafka_topic('temperature')
    print('topic populated')

    yield

    # Tear down: empty the 'test' kafka topic, stop flask server, kafka and zookeper
    os.system("ps ax | grep -i 'python consumer/server.py' | grep -v grep | awk '{print $1}' | xargs kill -SIGTERM")
    print('server stopped')
    _delete_kafka_topic('temperature')
    print('topic deleted')
    os.system('kafka-server-stop /usr/local/etc/kafka/server.properties')
    os.system("ps ax | grep -i 'zookeeper' | grep -v grep | awk '{print $1}' | xargs kill -SIGINT")
    print('zookepper and kafka stopped')


def _populate_kafka_topic(topic_name):
    """Send a few test values to the given kafka topic running locally."""
    producer = KafkaProducer(bootstrap_servers='localhost:9092')
    for value in range(10):
        producer.send(topic_name, bytes([value]))
        time.sleep(1)


def _delete_kafka_topic(topic_name):
    """Delte the given kafka topic running locally."""
    kafka_client = KafkaAdminClient(bootstrap_servers='localhost:9092')
    kafka_client.delete_topics([topic_name])
