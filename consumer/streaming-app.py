"""Read sensor data from a Kafka stream and compute a few metrics in near real time."""

from pyspark.sql import SparkSession, Row
import pyspark.sql.functions as F
from pyspark.sql.types import IntegerType


def start_spark():
    """Init and return a Spark Session."""
    return SparkSession.builder \
        .appName('DataModeling') \
        .master('local[4]') \
        .getOrCreate()


def get_logger(spark):
    """Configure logger (disable needless noisy logs)."""
    log4jLogger = spark.sparkContext._jvm.org.apache.log4j
    log4jLogger.LogManager.getLogger('org').setLevel(log4jLogger.Level.ERROR)
    log4jLogger.LogManager.getLogger('akka').setLevel(log4jLogger.Level.ERROR)
    return log4jLogger.LogManager.getLogger(__name__)


def read_input_stream(spark):
    """Read from Kafka using Spark structured streaming."""
    return spark \
        .readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", "localhost:9092") \
        .option("subscribe", "temperature,humidity,pressure") \
        .load()


def process_data(df):
    """Process stream data, compute metrics and display live result to the console."""

    # map() on dataframe does not exist in PySpark and passing through an rdd as we would do 
    # in batch mode is not allowed by the structured streaming API so we have to use a UDF. 
    spark.udf.register('deserializeInput', lambda x: int.from_bytes(x, byteorder='big'), IntegerType())
    return df \
	.select('topic', 'value') \
	.withColumnRenamed('topic', 'sensor') \
	.selectExpr('sensor', 'deserializeInput(value) as value') \
	.groupBy('sensor').agg(
	    F.count('value').alias('count'),
	    F.min('value').alias('minimum'),
	    F.max('value').alias('maximum'),
	    F.avg('value').alias('average')
	) \
	.writeStream \
	.outputMode('complete') \
	.format('console') \
	.start()


if __name__ == '__main__':

    spark = start_spark()
    logger = get_logger(spark)
    logger.info('Spark application started')
    df = read_input_stream(spark)
    query = process_data(df)
    query.awaitTermination()
