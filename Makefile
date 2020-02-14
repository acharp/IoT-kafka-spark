PIP := .venv/bin/pip
SPARK_BINARIES := spark-2.4.4-bin-hadoop2.7.tgz
SPARK_SUBMIT := spark/spark-2.4.4-bin-hadoop2.7/bin/spark-submit
SPARK_SQL_KAFKA_PKG := org.apache.spark:spark-sql-kafka-0-10_2.11:2.4.4

install:
	# Install spark
	mkdir spark
	wget -P spark/ http://mirror.serverion.com/apache/spark/spark-2.4.4/$(SPARK_BINARIES)
	tar -xvzf spark/$(SPARK_BINARIES) -C spark/
	# Install python dependencies
	virtualenv .venv
	$(PIP) install -r requirements.txt

build:
	# Build sensor containers
	docker-compose build

run:
	# Start zookeper and kafka
	nohup zookeeper-server-start /usr/local/etc/kafka/zookeeper.properties > /dev/null 2>&1 &
	sleep 2
	nohup kafka-server-start /usr/local/etc/kafka/server.properties > /dev/null 2>&1 &
	sleep 2
	# Start sensors
	docker-compose up -d
	sleep 2
	# Start flask webserver
	# . .venv/bin/activate; nohup python consumer/server.py > /dev/null 2>&1 &
	. .venv/bin/activate; nohup python consumer/server.py > prodserverlogs &
	# Start streaming app
	. .venv/bin/activate; JAVA_HOME=$$(/usr/libexec/java_home -v 1.8) $(SPARK_SUBMIT) --packages $(SPARK_SQL_KAFKA_PKG) consumer/streaming-app.py

stop:
	# Stop flask webserver
	ps ax | grep -i 'python consumer/server.py' | grep -v grep | awk '{print $$1}' | xargs kill -SIGINT
	# Stop sensors
	docker-compose stop
	# Stop kafka
	-kafka-server-stop /usr/local/etc/kafka/server.properties
	# Stop zookeper
	ps ax | grep -i 'zookeeper' | grep -v grep | awk '{print $$1}' | xargs kill -SIGINT

clean:
	rm -rf spark
	rm -rf .venv
	rm wget-log
