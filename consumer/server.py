from datetime import datetime
import json
import statistics

from flask import Flask, request, Response
from kafka import KafkaConsumer, TopicPartition


METRICS = ('count', 'min', 'max', 'average')
SENSORS = ('temperature', 'humidity', 'pressure')
TIMESTAMP_FORMAT = '%Y-%m-%d %H:%M:%S'
KAFKA_SOCKET = 'localhost:9092'

app = Flask(__name__)


def validate_request_body(body):
    """Validate incoming request body."""
    errors, from_tstamp, to_tstamp = validate_tstamp(body)
    if errors:
        return errors, {}
    errors, operations = filter_wrong_input(body)
    return errors, operations, from_tstamp, to_tstamp


def validate_tstamp(body):
    """Check that the timeframe requested is valid."""
    if 'from' not in body or 'to' not in body:
        return ['Keys "from" and "to" are required'], '', ''
    try:
        from_tstamp = datetime.strptime(body['from'], TIMESTAMP_FORMAT)
        to_tstamp = datetime.strptime(body['to'], TIMESTAMP_FORMAT)
    except ValueError:
        return ['Incorrect input timestamp format, should be YYYY-MM-DD hh:mm:ss'], '', ''
    if from_tstamp > to_tstamp:
        return ['"from" has to be earlier than "to"'], '', ''
    return [], from_tstamp, to_tstamp


def filter_wrong_input(body):
    """
        Filter out wrong fields from the request body.
        Returns list of errors and dict of operations to compute like {"temperature": ["count", "min"], "pressure": ["count", "min"]}
    """
    errors = []
    operations = {}

    # Parse resquest body to keep only metrics and sensors expected
    for key, value in body.items():
        if key in ('from', 'to'):
            continue
        elif key in SENSORS:
            for metric in value:
                if metric in METRICS:
                    if key not in operations.keys():
                        operations[key] = [metric]
                    else:
                        operations[key].append(metric)
                else:
                    errors.append('Unexpected metric {} to compute for the sensor {}'
                                  .format(metric, key))
        else:
            errors.append('Unexpected key {} in the request body'.format(key))

    return errors, operations


def compute_operations(operations, from_tstamp, to_tstamp):
    """Compute the metrics requested."""
    result = {}
    metric_functions = {'average': statistics.mean, 'min': min, 'max': max, 'count': len}

    for sensor, metrics in operations.items():
        # Get kafka offsets matching timestamps requested
        consumer = KafkaConsumer(sensor, bootstrap_servers=KAFKA_SOCKET,
                             value_deserializer=lambda x: int.from_bytes(x, byteorder='big'))
        partition = TopicPartition(sensor, 0)
        start_offset = consumer.offsets_for_times(
             {partition: int(round(from_tstamp.timestamp() * 1000))})[partition].offset
        end_offset = consumer.offsets_for_times(
            {partition: int(round(to_tstamp.timestamp() * 1000))})[partition].offset
        # Read values and compute metrics requested
        values = get_kafka_values(consumer, partition, start_offset, end_offset)
        result[sensor] = {metric: metric_functions[metric](values) for metric in metrics}

    return result


def get_kafka_values(consumer, partition, start_offset, end_offset):
    """Consume Kafka data between two offsets and return record values."""
    values = []
    consumer.seek(partition, start_offset)
    for msg in consumer:
        if msg.offset > end_offset:
            break
        else:
            values.append(msg.value)
    return values


def build_response(errors, result):
    """Build HTTP response depending on errors and result."""
    response_body = json.dumps({'result': result, 'errors': errors})
    status_code = 200
    if errors and not result:
        status_code = 400
    return Response(response_body, status=status_code, mimetype='application/json')


@app.route('/health', methods=['GET'])
def health_check():
    return {"status": "Healthy!"}


@app.route('/compute/metrics', methods=['POST'])
def compute_metrics():
    if not request.json or request.json == {}:
        return Response('{"bad request": "body must be valid non empty json"}',
                        status=400, mimetype='application/json')
    errors, operations, from_tstamp, to_tstamp = validate_request_body(request.json)
    result = compute_operations(operations, from_tstamp, to_tstamp)
    return build_response(errors, result)


if __name__ == '__main__':
    app.run()
