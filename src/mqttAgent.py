#===============================================================================
# MQTT Agent - Manage connection and routing of messages with MQTT Hub
#===============================================================================

import paho.mqtt.client as mqtt
import json
import time
import logging
import mqttTopicHelper as topicHelper
from mqttObserver import MQTTObserver
from mqttRouter import MQTTRouter
from socket import error as socket_error

#===============================================================================
# MQTT Agent Class
#===============================================================================
class MQTTAgent(mqtt.Client):
    
    #===========================================================================
    # Constructor
    #===========================================================================
    def __init__(self, client_id):
        super().__init__(client_id)
        self.xMqttUser = ""
        self.xMqttPwd = ""
        self.xDiconnectedTopic=""
        self.xConnectedTopic=""
        self.xMqttTarget = ""
        self.xMqttPort = 1883
        self.xReconnect = False
        self.xLogging = logging.getLogger(__name__)
        self.xObservers = []
        self.xRouters = []
        
        self.xDiconnectedTopic = topicHelper.genLifeCycleTopic(
            client_id, topicHelper.MQTT_TOPIC_LIFECYCLE_OFFLINE)
        self.xConnectedTopic = topicHelper.genLifeCycleTopic(
            client_id, topicHelper.MQTT_TOPIC_LIFECYCLE_ONLINE)

        
    #===========================================================================
    # Define credentials
    #===========================================================================
    def credentials(self, mqttUser : str, mqttPwd : str):
        self.xMqttUser = mqttUser
        self.xMqttPwd = mqttPwd
        
    #===========================================================================
    # Set up the target MQTT Hub to talk to
    #===========================================================================
    def mqttHub(self, mqttTarget: str, mqttPort: int, recon: bool=False, ca_cert: str=None):
        self.xMqttTarget = mqttTarget
        self.xMqttPort = mqttPort
        self.xReconnect = recon
        self.username_pw_set(username=self.xMqttUser, password=self.xMqttPwd)
        self.ca_cert = ca_cert
        if (self.ca_cert != None):
            self.tls_set(ca_certs=self.ca_cert)
            self.xLogging.debug("Setup TLS cert")
        #self.start()
        
    #===========================================================================
    # Start task connecting and responding
    #===========================================================================
    def start(self):     
        self.doConnect()            
        self.loop_forever()
     
    #===========================================================================
    # Connect to the MQTT Hub
    #===========================================================================
    def doConnect(self):
        j = {'online':0}
        p = json.dumps(j)
        self.will_set(self.xDiconnectedTopic, p, qos=1, retain=False) #set will  
        conn=False
        while not conn:
            try:
                self.connect(self.xMqttTarget, self.xMqttPort, keepalive=30)
                conn=True
            except socket_error as serr:
                if (self.xReconnect):
                    self.xLogging.info("Connection Error - retying")
                    time.sleep(2)
                else:
                    conn=True
                    self.xLogging.info("Connection Failed")
                 
        j = {'online':1}
        p = json.dumps(j)
        infot = self.publish(self.xConnectedTopic,p,retain=False,qos=1)
        self.xLogging.info("MQTT Connection Established")

            
    #===========================================================================
    # On Connection call back.
    #===========================================================================
    def on_connect(self, mqttc, obj, flags, rc, properties=None):
        self.xLogging.debug("Connected")
        for o in self.xObservers:
            o.online()
        for r in self.xRouters:
            r.subscribe(self)
        return
    
    #===========================================================================
    # On message call back, trigger the routers
    #===========================================================================
    def on_message(self, mqttc, obj, msg):
        self.xLogging.debug("Received topic %s payload %s"%(msg.topic, str(msg.payload)))
        for o in self.xObservers:
            o.received()
        for r in self.xRouters:
            try:
                if (r.route(msg.topic, msg.payload, self)):
                    return
            except Exception as e:
                self.xLogging.exception("Error occurred while routing message")
      
    #=======================================================================
    # on disconnect callb ack. 
    #=======================================================================
    def on_disconnect(self, client, userdata, rc, properties=None):
        self.xLogging.debug("Disconnected %d"%rc)
        for o in self.xObservers:
            o.offline()
        if (rc != 0):
            if (self.xReconnect):
                self.doConnect()
         
   #========================================================================
   # on publish call back
   #========================================================================
    def on_publish(self, client, userdata, mid, properties=None):
        for o in self.xObservers:
            o.sent()
    
    #===========================================================================
    # Add observer to listen to connection and disconnect events
    #===========================================================================
    def addObserver(self, o: MQTTObserver):
        self.xObservers.append(o)    
    
    #===========================================================================
    # Add a router to handle messages
    #===========================================================================
    def addRouter(self, router: MQTTRouter):
        self.xRouters.append(router)
    