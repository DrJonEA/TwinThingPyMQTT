#===============================================================================
# Client for a Twin Mgr to cache state of things and provide query capability
# Jon Durrant
# 14-Jan-2022
#===============================================================================
from mqttAgent import  MQTTAgent
import logging
from mqttObserver import MQTTObserver
from mqttRouterPing import MQTTRouterPing
from twinMgrStateRouter import TwinMgrStateRouter
from mqttRouterTwin import MQTTRouterTwin
import os

from twinState import TwinState
import threading

LOGLEVEL = os.environ.get('LOGLEVEL', 'INFO').upper()
logging.basicConfig(level=LOGLEVEL, 
                    format= '[%(asctime)s] {%(name)s:%(lineno)d} %(levelname)s - %(message)s')



#Credentials = needs to look at picking up from network
mqttUser=os.environ.get("MQTT_USER")
mqttPwd=os.environ.get("MQTT_PASSWD")
mqttTarget= os.environ.get("MQTT_HOST")
mqttPort=int(os.environ.get("MQTT_PORT"))
mqttCert=os.environ.get("MQTT_CERT", None)

logging.info("MQTT %s:%d User:%s"%(mqttTarget, mqttPort, mqttUser))

dbUser = os.environ.get("TWIN_DB_USER")
dbPwd = os.environ.get("TWIN_DB_PASSWD")
dbHost = os.environ.get("TWIN_DB_HOST")
dbPort = int(os.environ.get("TWIN_DB_PORT"))
dbSchema = os.environ.get("TWIN_DB_SCHEMA")

logging.info("Twin DB %s:%d Scheme:%s User:%s"%(dbHost, dbPort, dbSchema, dbUser))

#Setup the state. Have some stats on behaviour
state = TwinState()
state.setState({
    'trn': 1,
    'things': 0,
    'cache': 0
    })

#Setup the Client Agent
mqttAgent = MQTTAgent(mqttUser)
mqttAgent.credentials(mqttUser, mqttPwd)
mqttAgent.mqttHub(mqttTarget, mqttPort, True, mqttCert)

#Set up the observers and routers
mqttObs = MQTTObserver()
pingRouter = MQTTRouterPing(mqttUser)
stateRouter = TwinMgrStateRouter(mqttUser, state, mqttAgent)
twinRouter = MQTTRouterTwin(state, mqttUser, dbHost, dbPort, dbSchema, dbUser, dbPwd )

#Add observers and reotuers to the agent
mqttAgent.addObserver(mqttObs)
mqttAgent.addRouter(pingRouter)
mqttAgent.addRouter(stateRouter)
mqttAgent.addRouter(twinRouter)

#Timer for housekeeping
xTimer = None
def housekeeping():
    print("Housekeeping")
    twinRouter.cacheHousekeeping(60.0*15) # 15 minutes
    twinRouter.logHousekeeping(60*60*24*7) # 7 Days
    xTimer = threading.Timer(60.0*60.0, housekeeping)
    xTimer.start()

xTimer = threading.Timer(60.0*15, housekeeping)
xTimer.start()

#Start the agent
mqttAgent.start()