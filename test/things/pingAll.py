import paho.mqtt.client as mqtt
import paho.mqtt as paho
import json
import time
import os
import sys

if (len(sys.argv) != 2):
    print("Require target ID as parater")
    sys.exit()


print('paho version', getattr(paho,'__version__', 'unknown'))
print('client module', mqtt.__file__)

targetId = sys.argv[1]


user=os.environ.get("MQTT_USER")
passwd=os.environ.get("MQTT_PASSWD")
host= os.environ.get("MQTT_HOST")
port=int(os.environ.get("MQTT_PORT"))
print("MQTT %s:%d - %s\n"%(host,port, user))

ping_topic = "GRP/ALL/TPC/PING"
connected_topic = "TNG/" + user + "/LC/ON"
disconnected_topic = "TNG/" + user + "/LC/OFF"

#pong_topic = "TNG/" + targetId + "/TPC/PONG"
pong_topic = "TNG/+/TPC/PONG"
lc_topic = "TNG/" + targetId + "/LC/#"

# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc, properties=None):
    print("Connected with result code "+str(rc))

    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    


# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    print("Rcv topic=" +msg.topic+" msg="+str(msg.payload))

client = mqtt.Client(client_id=user)
client.username_pw_set(username=user, password=passwd)
client.on_connect = on_connect
client.on_message = on_message
j = {'online':0}
p = json.dumps(j)
client.will_set(disconnected_topic, p, qos=1, retain=False) #set will

client.connect(host, port, 60)

client.loop_start()

client.subscribe( lc_topic )
client.subscribe( pong_topic )
    
print("publishing connect")
j = {'online':1}
p = json.dumps(j)
client.publish(connected_topic,p,retain=False,qos=1)

pingId = 0;
j = {'id': pingId}
p = json.dumps(j)
print("Publishing ping %s"%p)
infot = client.publish(ping_topic, p,retain=False, qos=1)
infot.wait_for_publish()
pingId = pingId + 1

time.sleep(30)