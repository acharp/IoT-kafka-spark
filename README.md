## Goal
This project simulates 3 IoT sensors continuously producing data which we collect and use in two ways:
- A live data pipeline updating metrics (i.e. count, mean, max, ...) as soon as new data arrive
- An HTTP server which can be requested to compute some metrics over a specific time window

## Architecture
The 3 IoT sensors are simple scripts run in docker containers through the `docker-compose.yml` file. Their code can be found in the `producer` folder. Each of them keep sending random integers between 0 to 100 to a dedicated kafka topic (1 topic per sensor).  
The Spark streaming app and the Flask webserver code can be found in the `consumer` folder. Both of them are directly plugged to the Kafka stream and compute aggregation metrics per sensor.

## Running and using the project

### Pre-requesites (and the instructions to install them on Mac):
- java 8 (because of pyspark):  
    `brew tap caskroom/versions`  
    `brew cask install java8`
- python3 and virtualenv:  
    `brew install python3`  
    `pip install virtualenv`
- Local zookeper and kafka installation:  
    `brew install kafka`
- docker and docker-compose:  
    just get docker desktop: https://docs.docker.com/docker-for-mac/install/

### Run instructions:
- `make install` to download and install the dependencies needed
- `make build` to build the IoT sensor images
- `make run` to run the whole project: the 3 sensors, kafka, spark streaming app and the flask server
-  when you're done playing around, use Ctrl-C to stop the interactive spark streaming app and `make stop` to stop all the stuff started in the background during the previous step
- `make clean` to delete the dependencies downloaded and logs created. Then you'll need to rerun `make install` again if you want to rerun the project.

### Usage instructions:
When executing `make run`, everything is run in the background except the Spark streaming app which stays in the foreground and displays to the console the metrics being updated live as soon as new data are sent to the Kafka stream.
To query the webserver, send requests to your `localhost:5000` socket. For example:
```
curl --location --request POST 'localhost:5000/compute/metrics' \
--header 'Content-Type: application/json' \
--data-raw '{
	"temperature" : ["count", "min"],
	"humidity" : ["average", "max"],
	"from": "2020-01-13 15:12:00",
	"to": "2020-01-13 15:13:00",
}'
```
Which gives the following response:
```
{
    "result": {
        "temperature": {
            "count": 61,
            "min": 2
        },
        "humidity": {
            "average": 48.557377049180324,
            "max": 98
        }
    },
    "errors": []
}
```
For the json body, the valid keys are "from", "to" and the name of the sensors : "temperature", "humidity" and "pressure".  
The metrics available to compute are "count", "average", "max" and "mean".  
If you include some unexpected keys or metrics in your request, the API will still work: it will compute the right keys in the `result` field and add an `errors` field describing the wrong input. For example the following request:
```
curl --location --request POST 'localhost:5000/compute/metrics' \
--header 'Content-Type: application/json' \
--data-raw '{
	"temperature" : ["count", "min", "wrongMetric"],
	"humidity" : ["average", "max"],
	"from": "2020-01-13 15:12:00",
	"to": "2020-01-13 15:13:00",
	"wrongKey": 1
}'
```
Gives the following response:
```
{
    "result": {
        "temperature": {
            "count": 61,
            "min": 2
        },
        "humidity": {
            "average": 48.557377049180324,
            "max": 98
        }
    },
    "errors": [
        "Unexpected metric wrongMetric to compute for the sensor temperature",
        "Unexpected key wrongKey in the request body"
    ]
}
```
And if you include only unexpected keys then the API will answer with a 400 status code and an empty result field. For example the following request:
```
curl --location --request POST 'localhost:5000/compute/metrics' \
--header 'Content-Type: application/json' \
--data-raw '{
	"wrong" : ["wrongMetric"],
	"from": "2020-01-13 15:12:00",
	"to": "2020-01-13 15:13:00",
	"wrongKey": 1
}'
```
Will give the following response:
```
{
    "result": {},
    "errors": [
        "Unexpected key wrong in the request body",
        "Unexpected key wrongKey in the request body"
    ]
}
```

## Limitations

### General
- I have not been able to dockerize the whole project and run everything from a single docker-compose command because writing to a dockerized kafka with the kafka-python library turned out to be particularly tricky and wasted quite a lot of my time.
- Using Python to work with kafka and spark streaming is not optimal because:  
    - the python API lags a bit behind in terms of features. 
    - performances are slightly worse than the Scala/Java ones so if we are talking about a fully automated software where latency is a critical requirement, Python would not be the right fit.  
Scala or Java would be a better choice here.

### Streaming app
- No mechanism to filter duplicate datapoints from the sensor. We may process some without even noticing which would mess up the metrics outputted.
- No watermark nor rule to deal with delayed events. Could be a problem depending on how the data are used downstream the pipeline.

### HTTP server
- Organise the code in proper module and objects: at least 2 classes, one for RequestHandler and another one for KafkaReader to abstract the logic there in case we want to switch to another way to handle the request or another data layer.
- Instead of loading all the values read from Kafka in memory at once, use a generator to reduce the memory footprint. The downside would be to have to re-read the values for each metric we need to compute. Tradeoff between memory usage and execution time: since it is a live API and the data are small (simple integers) I chose to foster the execution time. 
- Requests are taking a few seconds when asking to compute several metrics for several sensors. To lower it down we could run several brokers (to have several kafka network socket serving data) and parallelize fetching the data for the different sensors.

