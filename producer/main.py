"""Send random temperature data to a kafka topic."""

import logging
import os
import random
import sys
import time

from kafka import KafkaProducer, KafkaConsumer


logging.basicConfig(stream=sys.stdout, level=logging.INFO)
log = logging.getLogger(__name__)


if __name__ == '__main__':

    kafka_socket = os.environ['KAFKA_SOCKET']
    kafka_topic = os.environ['KAFKA_TOPIC']
    producer_id = os.environ['PRODUCER_ID']

    producer = KafkaProducer(bootstrap_servers=kafka_socket, 
                             client_id=producer_id)
    while True:
        value = random.randrange(0, 100)
        # First time we send a message the topic will be created
        producer.send(kafka_topic, bytes([value]))
        log.info('Sent value "{}" to topic "{}"'.format(value, kafka_topic)) 
        time.sleep(1)
