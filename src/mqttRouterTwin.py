#===============================================================================
# mqttRouterTwin - Router for Twin State Cache Management
# Jon Durrant
# 10-Jan-2022
#===============================================================================
import logging
from datetime import datetime, timedelta, timezone
import paho.mqtt.client as mqtt
from mqttRouter import MQTTRouter 
import mqttTopicHelper as topicHelper
from twinState import TwinState
from twinDb import TwinDb, TwinLog
from mqttGroup import MQTTGroup
from mqttTwin import MQTTTwin
from twinState import TwinState
import twinProtocol
import json
from sqlalchemy import exc
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from itertools import groupby

class MQTTRouterTwin(MQTTRouter):
    
    #=======================================================================
    # Constructor
    # state: TwinState: state object that holds the states about the Twin management
    # client_id: str - Client id for this thing
    # dbHost: str - DB host
    # dbPort: int - port for the DB connection
    # dbSchema: str - DB Schema,
    # dbUser: str - User name for DB access 
    # dbPwd: str - password for DB access
    #=======================================================================
    def __init__(self, state: TwinState, client_id: str, dbHost: str, dbPort: int, dbSchema: str,
                 dbUser: str, dbPwd: str):
        super().__init__(client_id)
        self.xState = state
        self.xLogging = logging.getLogger(__name__)
        
        self.xSet = topicHelper.getTwinSet("+")
        self.xGet = topicHelper.getTwinGet("+")
        
        self.xLC = topicHelper.genLifeCycleTopic("+", topicHelper.MQTT_TOPIC_LIFECYCLE_ONLINE)
        self.xUpdate = topicHelper.getThingUpdate("+")
        
        self.xGrpSet = topicHelper.getTwinGroupSet("+")
        self.xGrpGet = topicHelper.getTwinGroupGet("+")

        self.xGrpLog = topicHelper.genGroupTopic(
            topicHelper.MQTT_GRP_ALL, 
            topicHelper.MQTT_TOPIC_LOG)
        
        self.xCache = {}
        
        self.connectStr='mysql+pymysql://%s:%s@%s:%d/%s'%(
            dbUser,
            dbPwd,
            dbHost,
            dbPort,
            dbSchema
            )
        self.session=None
        self.openDb()
        
    #===========================================================================
    # Open the DB, local used function
    #===========================================================================
    def openDb(self):
        try:
            #self.xLogging.info("DB:" + self.connectStr)
            engine = create_engine(self.connectStr)
            session = sessionmaker()
            session.configure(bind=engine)
            self.session=session()
            
            #set Count
            fakeTwin = TwinDb("UNKNOWN")
            count = fakeTwin.getTwinCount(self.session)
            delta = {
                'things': count
            }
            self.xState.updateState(delta)
        except exc.SQLAlchemyError:
            self.xLogging.error("Failed to open DB")
            self.session = None
        
   #========================================================================
   # Subscribe to the Get and Set twin and groups
   # Also subscrine to LC connects
   #========================================================================
    def subscribe(self, interface: mqtt):
        interface.subscribe(self.xGet, qos=1)
        interface.subscribe(self.xSet, qos=1)
        interface.subscribe(self.xLC, qos=1)
        interface.subscribe(self.xUpdate, qos=1)
        interface.subscribe(self.xGrpGet, qos=1)
        interface.subscribe(self.xGrpSet, qos=1)
        interface.subscribe(self.xGrpLog, qos=1)
        
    #=======================================================================
    # Route the published messahes
    #=======================================================================
    def route(self, topic: str, payload: str, interface: mqtt):
        #Twin  Get
        if ( topicHelper.topicEquals(self.xGet, topic)):
            target = self.tngTarget(topic)
            j = json.loads(payload)
            if ("select" in j):
                target = self.tngTarget(topic)
                j = json.loads(payload)
                self.twinGet(target, j, interface)
            else:
                twin = self.getTwin(target, interface)
                self.pubUpdated(target, twin, interface)
                
            return True
        
        #Twin Set
        if ( topicHelper.topicEquals(self.xSet, topic)):
            target = self.tngTarget(topic)
            j = json.loads(payload)
            self.twinSet(target, j, interface)
            return True
        
        #THing Online Sequence
        if ( topicHelper.topicEquals(self.xLC, topic)):
            target = self.tngTarget(topic)
            if (not self.isNewTwin(target)):
                
                twin = self.getTwin(target, interface)
                
                setTopic = topicHelper.getThingSet(target)
                setState = {'state': twin.getReportedState()}
                #setState = {'delta': twin.getReportedState()}
                self.xLogging.debug("Set state on returning thing %s state %s"%(target, json.dumps(setState,sort_keys=True) ))
                interface.publish(setTopic, json.dumps(setState), retain=False, qos=1)
                
                if (not twin.isUptoDate()):
                    deltaState = {'delta': twin.getDelta()}
                    self.xLogging.debug("Set delta for returning thing %s delta %s"%(target, json.dumps(deltaState,sort_keys=True)))
                    interface.publish(setTopic, json.dumps(deltaState), retain=False, qos=1)
                
            else:
                self.xLogging.debug("Unknown thing, so requesting get %s"%target)
                getTopic = topicHelper.getThingGet(target)
                interface.publish(getTopic, "{'GET': 1}", retain=False, qos=1)
                
            
            self.xLogging.debug("LC event on %s"%topic)
            return True
            
        #Habdle Update from Thing
        if (topicHelper.topicEquals(self.xUpdate, topic)):
            target = self.tngTarget(topic)
            n = self.isNewTwin(target)
            twin = self.getTwin(target, interface)
            j = json.loads(payload)
            if ("delta" in j):
                twin.updateFromThing(j["delta"])
                if (n):
                    getTopic = topicHelper.getThingGet(target)
                    interface.publish(getTopic, "{'GET': 1}", retain=False, qos=1)
                
            elif ("state" in j):
                twin.stateFromThing(j["state"])
                #self.xLogging.debug("Twin %s state Payload %s"%(target, payload))
            
            self.xLogging.debug("Twin %s Reported %s"%(target, json.dumps(twin.getReportedState(), sort_keys=True)))
            self.pubUpdated(target, twin, interface)
            self.storeTwin(twin)
            return True
        
        #Group Set
        if (topicHelper.topicEquals(self.xGrpSet, topic)):
            grp = self.tngTarget(topic)
            j = json.loads(payload)
            self.groupSet(grp, j, interface)
            return True
            
        #Group Get
        if (topicHelper.topicEquals(self.xGrpGet, topic)):
            grp = self.tngTarget(topic)
            j = json.loads(payload)
            self.groupGet(grp, j, interface)
            return True

        if (topicHelper.topicEquals(self.xGrpLog, topic)):
            j = json.loads(payload)
            self.writeLog(
                j["level"], 
                j["msg"], 
                j.get("detail", ""),
                j["service"], 
                j["source"], 
                j["sourceTS"]
                )
        return False
        
    #===========================================================================
    # Split out the target ID or group from the topic
    #===========================================================================
    def tngTarget(self, topic: str):
        target = topic.split("/")[1]
        
        return target
    
    #===========================================================================
    # Get the twin based on it's client id
    # target: str, - Client id of the target thing
    # interface: mqtt - mqtt interface to allow request of a get
    #===========================================================================
    def getTwin(self, target: str, interface: mqtt):
        self.xLogging.debug("****GET TWIN %s"%target)
        if (not target in self.xCache):
            self.xLogging.debug("Twin not in cache %s"%target)
            self.xCache[target] = TwinDb(target)
            try:
                if (self.xCache[target].loadFromDb(self.session)):
                    self.xLogging.debug("Twin %s loaded from DB"%target)
                    twin = self.xCache[target]
                    setTopic = topicHelper.getThingSet(target)
                    setState = {'state': twin.getReportedState()}
                    self.xLogging.debug("Set state on returning thing %s state %s"%(target, json.dumps(setState,sort_keys=True) ))
                    interface.publish(setTopic, json.dumps(setState), retain=False, qos=1)
                    
                    if (not twin.isUptoDate()):
                        deltaState = {'delta': twin.getDelta()}
                        self.xLogging.debug("Set delta for returning thing %s delta %s"%(target, json.dumps(deltaState,sort_keys=True)))
                        interface.publish(setTopic, json.dumps(deltaState), retain=False, qos=1) 
                
                    #Update Cache Stats
                    delta = {
                        'cache': self.xState.getState().get('cache', 0)+1
                    }
                    self.xState.updateState(delta)
                
                else:
                    self.xLogging.debug("Twin %s not in DB"%target)
                    getTopic = topicHelper.getThingGet(target)
                    interface.publish(getTopic, "{'GET': 1}", retain=False, qos=1)
                    
                     #Update Cache Stats
                    delta = {
                        'cache': self.xState.getState().get('cache', 0)+1,
                        'things': self.xState.getState().get('things', 0)+1,
                    }
                    self.xState.updateState(delta)
                    
            except exc.SQLAlchemyError:
                self.xLogging.error("Failed to read from DB, reopen")
                self.openDb()
        else:
            self.xLogging.debug("Twin in cache %s"%target)    
            
        return self.xCache[target]
      
      
    #===========================================================================
    # Is the twin new and not in the DB
    # target - client_id of the thing
    #===========================================================================
    def isNewTwin(self, target: str):
        if (not target in self.xCache):
            twin = TwinDb(target)
            #self.xCache[target] = twin
            try:
                if (twin.loadFromDb(self.session)):
                    return False
                else:
                    return True
            except exc.SQLAlchemyError:
                self.xLogging.error("Failed to read from DB, reopen")
                self.openDb()
                
            return True
        else:       
            return False
    
    #===========================================================================
    # Publish update of a twin to the UPD channel. Has full reported status
    #===========================================================================
    def pubUpdated(self, target: str, twin: TwinDb, interface: mqtt):
        upd = { "desired": twin.getDesiredState(),
               "desiredMeta": twin.getDesiredMeta(),
               "reported": twin.getReportedState(),
               "reportedMeta": twin.getReportedMeta(),
               "declined": twin.getDeclinedState(),
               "declinedMeta": twin.getDeclinedMeta()
        }
        updTopic = topicHelper.getTwinUpdate(target)
        interface.publish(updTopic, json.dumps(upd), retain=False, qos=1)
            
    #===========================================================================
    # Stoew the twin into the database
    #===========================================================================
    def storeTwin(self, twin: TwinDb):  
        try:
            twin.updateDb(self.session)
        except exc.SQLAlchemyError:
            self.xLogging.error("Failed to write to DB, reopen")
            self.openDb()
       
    #===========================================================================
    # Handle a Twin set request
    #===========================================================================
    def twinSet(self, target: str, j: dict, interface: mqtt):
        twin = self.getTwin(target, interface)
        newStates = {}
        if ("set" in j):
            newStates = j["set"]
        elif ("delta" in j):
            newStates = j["delta"]
        elif ("state" in j):
            newStates = j["state"]
        else:
            self.xLogging.error("Unknown format for set  %s"%json.dumps(j))
            return 
        
        #Update twin
        self.xLogging.debug("Updating with %s"%json.dumps(newStates, sort_keys=True))
        twin.updateDesiredState(newStates)
        self.storeTwin(twin)
        self.pubUpdated(target, twin, interface)
        
        #Update thing
        setTopic = topicHelper.getThingSet(target)
        delta = json.dumps({"delta": twin.getDelta()})
        self.xLogging.debug("Sending Thing delta->  %s"%delta)
        interface.publish(setTopic, delta, retain=False, qos=1)
                
    #===========================================================================
    # Handle a group set request
    #===========================================================================
    def groupSet(self, grp: str, d: dict, interface: mqtt):
        mGroup = MQTTGroup(grp)
        allGroup = mGroup.getGroupTwinIds(self.session)
        targets=[]
        reqTargets = d.get("from", [])
        if (len(reqTargets) == 0):
            targets = allGroup
        else:
            #Validate that target is in group
            for t in reqTargets:
                if (t in allGroup):
                    targets.append(t)
                else:
                    self.xLogging.info("Attempted to post to clientId that is not in group %s"%self.session)
        
        for target in targets:
            self.twinSet(target, d, interface)
            
    #===========================================================================
    # Handle a group get request. This will be a query structure
    #===========================================================================
    def groupGet(self, grp: str, d: dict, interface: mqtt):
        mGroup = MQTTGroup(grp)
        select = d.get("select", ["*"])
        columnAs = d.get("as",  [])           
        where = d.get("where", {})
        orient = d.get("orient", "records")
        query = d.get("query", 0)                 

        s = mGroup.selectTwinFrame(self.session, select, columnAs, where, orient)
        j = {
                "query": query,
                "res": json.loads(s)
            }
        topic = topicHelper.getTwinGroupResult(grp)
        interface.publish(topic, json.dumps(j), retain=False, qos=1)
        
    #=======================================================================
    # Handle a twin get request of query format
    #=======================================================================
    def twinGet(self, target: str, d: dict, interface: mqtt):
        mTwin = MQTTTwin(target)
        select = d.get("select", ["*"])
        columnAs = d.get("as",  [])           
        where = d.get("where", {})
        orient = d.get("orient", "records")
        query = d.get("query", 0)                 

        s = mTwin.selectTwinFrame(self.session, select, columnAs, where, orient)
        j = {
                "query": query,
                "res": json.loads(s)
            }
        topic = topicHelper.getTwinResult(target)
        interface.publish(topic, json.dumps(j), retain=False, qos=1)
        
    #=======================================================================
    # Cach housekeep to remoev items older that parameter from the cache
    #=======================================================================
    def cacheHousekeeping(self, removeOlderSeconds: int):
        ms = removeOlderSeconds * 1000
        purgeList = []
        for target in self.xCache:
            twin = self.xCache[target]
            if (twin.timeSinceConversation() > ms):
                purgeList.append(target)
        
        for target in purgeList:
            del self.xCache[target]
        
        self.xLogging.debug("Purged %s", json.dumps(purgeList))
        
         #Update Cache Stats
        delta = {
            'cache': len(self.xCache)
        }
        self.xState.updateState(delta)
                
    #=======================================================================
    # Log to DB and to the log file
    #=======================================================================        
    def writeLog(
            self, 
            level: str, 
            msg: str, 
            detail: str,
            service: str, 
            source: str, 
            sourceTS: int):
        log_message = msg if not detail else "%s: %s" % (msg, detail)
        log_level = getattr(logging, level.upper(), logging.INFO)
        self.xLogging.log(log_level, "%s [%s] source=%s" % (log_message, service, source))

        if self.session is None:
            self.xLogging.error("Cannot write log: database session is unavailable")
            return False

        log_entry = TwinLog(
            level=level,
            msg=msg,
            detail=detail,
            service=service,
            source=source,
            sourceTS=datetime.fromtimestamp(sourceTS, tz=timezone.utc).replace(tzinfo=None),
            ts=datetime.now(timezone.utc).replace(tzinfo=None),
        )

        try:
            self.session.add(log_entry)
            self.session.commit()
            return True
        except exc.SQLAlchemyError:
            self.session.rollback()
            self.xLogging.exception("Failed to write log entry to twinlog")
            return False

    def logHousekeeping(self, removeOlderSeconds: int):
        if self.session is None:
            self.xLogging.error("Cannot perform log housekeeping: database session is unavailable")
            return

        cutoff_time = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(seconds=removeOlderSeconds)
        try:
            deleted_count = self.session.query(TwinLog).filter(TwinLog.ts < cutoff_time).delete()
            self.session.commit()
            self.xLogging.info("Purged %d log entries older than %d seconds", deleted_count, removeOlderSeconds)
        except exc.SQLAlchemyError:
            self.session.rollback()
            self.xLogging.exception("Failed to perform log housekeeping"    )