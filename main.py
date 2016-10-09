# coding=utf-8
# https://www.flowdock.com/rest/files/176120/XRC_csHG-3sZRCt0-6ZRdg/UNOFFICIAL_X32_OSC_REMOTE_PROTOCOL%20(1).pdf

import logging, json
from threading import Timer
from logging.handlers import RotatingFileHandler
import paho.mqtt.client as paho
import pythonx32.x32

import config

def on_connect(mosq, obj, rc):
    logging.info("Connect with RC " + str(rc))

def on_disconnect(client, userdata, rc):
    print "start on_disconnect"
    logging.warning("Disconnected (RC " + str(rc) + ")")
    # if rc != 0:
    try_reconnect(client)
    print "end on_disconnect"

def on_log(client, userdata, level, buf):
    logging.debug(buf)

# MQTT reconnect
def try_reconnect(client, time = 60):
    print "start try_reconnect"
    try:
        logging.info("Trying reconnect")
        client.reconnect()
    except:
        logging.warning("Reconnect failed. Trying again in " + str(time) + " seconds")
        Timer(time, try_reconnect, [client]).start()
    print "end try_reconnect"

def on_message(mosq, obj, msg):
    print "start on_message"
    logging.info(msg.topic + " " + str(msg.qos) + " " + str(msg.payload))

    set_prefix = config.topic + "set/"
    if msg.topic.startswith( set_prefix ):
        path = msg.topic[len(set_prefix) : ]
        try:
            pult.set_value("/" + path, json.loads(msg.payload))
        except Exception as e:
            logging.error("set failed: " + str(e))

    get_prefix = config.topic + "get/"
    if msg.topic.startswith( get_prefix ) and msg.payload == "get":
        path = msg.topic[len(get_prefix) : ]
        try:
            value = pult.get_value("/" + path)
            mqttc.publish(get_prefix + path, json.dumps(value))
        except Exception as e:
            logging.error("get failed: " + json.dumps(e))

    command_prefix = config.topic + "command"
    if msg.topic == command_prefix:
        logging.info("got command " + msg.payload)
        if msg.payload == "volume up":
            volchange(config.paths["volume"], config.volume_increment_db, db=True)
        if msg.payload == "volume down":
            volchange(config.paths["volume"], -config.volume_increment_db, db=True)
        # if msg.payload == "alarm":
        #     volchange(-action/playtrack, 1)

        output_prefix = "output "
        if msg.payload.startswith(output_prefix):
            output_name = msg.payload[len(output_prefix):-2]
            state = msg.payload[-1:]
            try:
                print output_name
                print state
                path = config.outputs[output_name] + "/mix/on"
                print path
                pult.set_value(path, int(state), readback = False)
            except Exception as e:
                raise(e)
                # print e

        input_prefix = "input "
        if msg.payload.startswith(input_prefix):
            input_name = msg.payload[len(input_prefix):]
            try:
                logging.info('Trying to switch to "%s"' % input_name)
                path = config.inputs[input_name]
                logging.info('Path %s' % path)
                switch_input_to(path)
            except Exception as e:
                print e
                logging.error('Failed to switch to "%s"' % input_name)
    print "end on_message"

## Port from unofficial manual: Appendix – Converting X32 fader data to decibels and vice-versa
def float_to_db(f):
    if (f >= 0.5):
        db = f * 40. - 30. # max dB value: +10
    elif (f >= 0.25):
        db = f * 80. - 50.
    elif (f >= 0.0625):
        db = f * 160. - 70.
    elif (f >= 0.0):
        db = f * 480. - 90. # min db value: -90
    return db

def db_to_float(db):
    if (db < -60.):
        f = (db + 90.) / 480.
    elif (db < -30.):
        f = (db + 70.) / 160.
    elif (db < -10):
        f = (db + 50.) / 80.
    elif (db <= 10.):
        f = (db + 30.) / 40.
    return f


def volchange(path, amount, db=False):
    try:
        curr_value = pult.get_value(path)[0]
        if db:
            curr_value_db = float_to_db(curr_value)
            new_value_db = curr_value_db + amount
            new_value = db_to_float(new_value_db)
        else:
            new_value = curr_value + amount
        if new_value > 1.0:
            new_value = 1.0
        if new_value < 0.0:
            new_value = 0.0

        pult.set_value(path, new_value, readback = False)
    except Exception as e:
        logging.error("volchange failed: " + str(e))


def switch_input_to(path):
    for channel in range(1, 32):
        channel = str(channel) # Awsome hack for making it "01" instead of "1", which doesn't work
        if len(channel) == 1:
            channel = "0" + channel
        pult.set_value("/ch/" + channel + "/mix/on", 0, readback = False)

    for aux_channel in range(1, 8):
        aux_channel = str(aux_channel)
        if len(aux_channel) == 1:
            aux_channel = "0" + aux_channel
        pult.set_value("/auxin/" + aux_channel + "/mix/on", 0, readback = False)
    pult.set_value(path + "/mix/on", 1, readback = False)

    print pult.get_value(path + "/mix/fader")[0]
    if (pult.get_value(path + "/mix/fader")[0] < 0.2):
        pult.set_value(path + "/mix/fader", 0.5, readback = False)


logging.basicConfig(format='[%(levelname)s] %(asctime)s %(message)s', datefmt='%Y-%m-%d %H:%M:%S', level=logging.INFO)
file_handler = RotatingFileHandler("/home/mumalab/mqtt2x32/mqtt2x32.log", maxBytes=4000, backupCount=2)
logger = logging.getLogger()
logger.addHandler(file_handler)

# initialize MQTT
logging.info("Initializing MQTT")
mqttc = paho.Client("asdfadshkf", clean_session=True)
mqttc.username_pw_set(config.broker["user"], config.broker["password"])
mqttc.connect(config.broker["hostname"], config.broker["port"], 60)
mqttc.on_connect = on_connect
mqttc.on_disconnect = on_disconnect
mqttc.on_log = on_log
mqttc.on_message = on_message

mqttc.loop_start()
mqttc.subscribe(config.topic + "#", 0) # the '#' is a wildcard

# mqttc.publish(config.topic + "set/dca/1/fader", json.dumps([0.4])) # Use json like this to set/get values
# mqttc.publish(config.topic + "get/dca/1/fader", "get")

# connect to pult
pult = pythonx32.x32.BehringerX32("10.10.20.35", 10023, False)

while True:
    command = raw_input("-->")
    if (command == "ping"):
        print "pong"
    elif (command == "volup"):
        mqttc.publish(config.topic + "command", "volume up")
    elif (command == "voldown"):
        mqttc.publish(config.topic + "command", "volume down")
    elif (command == "test"):
        print mqttc
    elif (command == "reconnect"):
        try_reconnect(mq)

    elif (command.startswith("switch ")):
        prefix = "switch "
        suffix = command[len(prefix):]

        mqttc.publish(config.topic + "command", "input " + suffix)
