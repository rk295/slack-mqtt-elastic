#!/usr/bin/python -u
# -u to unbuffer stdout, plays nicer with supervisor

import sys
import json
import time
import os
import logging
import requests
import datetime as DT
from datetime import datetime

import paho.mqtt.client as paho
from pprint import pprint

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                    datefmt='%m-%d %H:%M')

logger = logging.getLogger(os.path.basename(__file__))

logger.debug('Starting...')

""" hostname and topic of MQTT """
hostname = os.getenv('MQTT_HOST')
topic = os.getenv('MQTT_TOPIC')
""" Optional username and password for MQTT """
username = os.getenv('MQTT_USERNAME', None)
password = os.getenv('MQTT_PASSWORD', None)

""" Optional Elastic config """
elastic_host = os.getenv('ELASTIC_HOST', 'localhost')
elastic_port = os.getenv('ELASTIC_PORT', '9200')
elastic_index = os.getenv('ELASTIC_INDEX', 'slack')
elastic_type = os.getenv('ELASTIC_TYPE', 'message')

fermat_url = os.getenv('FERMAT_URL', None)
fermat_username = os.getenv('FERMAT_USERNAME', None)
fermat_password = os.getenv('FERMAT_PASSWORD', None)

elastic_url = "http://" + elastic_host + ":" + \
    elastic_port + "/" + elastic_index + "/" + elastic_type
logger.debug("Will use elastic search URL %s" % elastic_url)


def to_fermat(message):

    if fermat_url is None:
        return

    logger.info("Posting to fermat at %s" % fermat_url)
    r = requests.post(fermat_url, data=json.dumps(message),
                      auth=(fermat_username, fermat_password))

    logger.debug("HTTP Status from fermat was %s" % (r.status_code))
    logger.debug("Response body from fermat was [%s]" % (r.text))

def on_message(client, userdata, message):
    """Called whenever a message is received. 

    """
    data = json.loads(message.payload)

    # Convert the slack EPOCH timestamp to ES preferred ISO format
    timestamp = data['timestamp']
    es_timestamp = DT.datetime.utcfromtimestamp(float(timestamp)).isoformat()
    data['@timestamp'] = es_timestamp

    r = requests.post(elastic_url, data=json.dumps(data))

    if r.status_code != 201:
        logger.debug("HTTP Status from elastic was %s" % (r.status_code))
        logger.debug("Response body from elastic was %s" % (r.json()))
    else:
        logger.debug("Message posted to ElasticSearch successfully")

    to_fermat(data)


def on_connect(client, userdata, rc):
    logging.debug("connected with result code=%s " % str(rc))


if __name__ == "__main__":

    # Bit hacky, making this global. But you know ;)
    switches = None

    mqttc = paho.Client()
    mqttc.message_callback_add(topic, on_message)

    mqttc.on_connect = on_connect
    if username is not None and password is not None:
        logging.debug("connected to MQTT with authentication")
        mqttc.username_pw_set(username, password)
    else:
        logging.debug("connected to MQTT without authentication")

    try:
        mqttc.connect(hostname)
    except Exception as e:
        logging.debug("failed to connect: %s" % e)

    logging.debug("subscribing to topic: %s" % topic)
    mqttc.subscribe(topic)

    while mqttc.loop() == 0:
        pass
