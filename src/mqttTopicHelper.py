

MQTT_TOPIC_THING_HEADER="TNG"
MQTT_TOPIC_HEADER="TPC"
MQTT_TOPIC_LIFECYCLE="LC"
MQTT_TOPIC_GROUP_HEADER="GRP"
MQTT_TOPIC_LIFECYCLE_OFFLINE="OFF"
MQTT_TOPIC_LIFECYCLE_ONLINE="ON"
MQTT_TOPIC_LIFECYCLE_KEEP_ALIVE="KEEP"
MQTT_TOPIC_LOG="LOG"
MQTT_STATE_TOPIC="STATE"
MQTT_STATE_TOPIC_UPDATE="UPD"
MQTT_STATE_TOPIC_GET="GET"
MQTT_STATE_TOPIC_SET="SET"
MQTT_TOPIC_PING="PING"
MQTT_TOPIC_PONG="PONG"
MQTT_GRP_ALL="ALL"
MQTT_TWIN_TOPIC="TWIN"
MQTT_STATE_TOPIC_RESULT="RES"




#===============================================================================
# /***
#  * generate the lifecycle topic for thing
#  * @param id - id of the thing
#  * @param name  = name of the lifecycle topic (ON, OFF, KEEP)
#  */
#===============================================================================
def genLifeCycleTopic(id: str, name: str):
    return ("%s/%s/%s/%s"%(MQTT_TOPIC_THING_HEADER, id,
            MQTT_TOPIC_LIFECYCLE, name  ))


#===============================================================================
# /***
#  * Generate the thing topic full name
#  * @param id - string id of the thing
#  * @param name - string name of the topic
#  */
#===============================================================================
def genThingTopic(id: str, name: str):
    return ("%s/%s/%s/%s"%(MQTT_TOPIC_THING_HEADER, id,
            MQTT_TOPIC_HEADER, name))

#===============================================================================
# /***
#  * Generate the group topic full name
#  * @param grp - string of group anme
#  * @param name - string name of the topic
#  */
#===============================================================================
def genGroupTopic(grp: str, name: str):
    return ("%s/%s/%s/%s"%(
            MQTT_TOPIC_GROUP_HEADER,
            grp,
            MQTT_TOPIC_HEADER,
            name))

 #==============================================================================
 # * Generate update topic for thing
 # * @param id - Id of thing
 #==============================================================================
def getThingUpdate(id: str):
    return ("%s/%s/%s/%s"%(MQTT_TOPIC_THING_HEADER, id,
            MQTT_STATE_TOPIC, MQTT_STATE_TOPIC_UPDATE))


 #==============================================================================
 # * Generate get topic for thing
 # * @param id - Id of thing
 #==============================================================================
def getThingGet( id: str):
    return ("%s/%s/%s/%s"%(MQTT_TOPIC_THING_HEADER, id,
                 MQTT_STATE_TOPIC, MQTT_STATE_TOPIC_GET))


#===============================================================================
#  * Generate set topic for thing
#  * @param id - Id of thing
# 
#===============================================================================
def getThingSet(id: str):
    return ("%s/%s/%s/%s"%(MQTT_TOPIC_THING_HEADER, id,
                 MQTT_STATE_TOPIC, MQTT_STATE_TOPIC_SET))
    
   
#============================================================================
# Get a twin get topic
# e.g. TNG/thing/TWIN/GET
#============================================================================
def getTwinGet(id: str):
    return ("%s/%s/%s/%s"%(MQTT_TOPIC_THING_HEADER, id,
                 MQTT_TWIN_TOPIC, MQTT_STATE_TOPIC_GET))

#============================================================================
# Get a twin set topic
# e.g. TNG/thing/TWIN/SET
#============================================================================
def getTwinSet(id: str):
    return ("%s/%s/%s/%s"%(MQTT_TOPIC_THING_HEADER, id,
                 MQTT_TWIN_TOPIC, MQTT_STATE_TOPIC_SET))
   
#============================================================================
# Get a twin update topic
# e.g. TNG/thing/TWIN/UPD
#============================================================================ 
def getTwinUpdate(id: str):
    return ("%s/%s/%s/%s"%(MQTT_TOPIC_THING_HEADER, id,
                 MQTT_TWIN_TOPIC, MQTT_STATE_TOPIC_UPDATE))
    
#============================================================================
# Get a twin result topic
# e.g. TNG/thing/TWIN/RES
#============================================================================
def getTwinResult(id: str):
    return ("%s/%s/%s/%s"%(MQTT_TOPIC_THING_HEADER, id,
                 MQTT_TWIN_TOPIC, MQTT_STATE_TOPIC_RESULT))
    
#============================================================================
# Get a grp get topic
# e.g. GRP/name/TWIN/GET
#============================================================================
def getTwinGroupGet(id: str):
    return ("%s/%s/%s/%s"%(MQTT_TOPIC_GROUP_HEADER, id,
                 MQTT_TWIN_TOPIC, MQTT_STATE_TOPIC_GET))
    
#============================================================================
# Get a grp set topic
# e.g. GRP/name/TWIN/SET
#============================================================================
def getTwinGroupSet(id: str):
    return ("%s/%s/%s/%s"%(MQTT_TOPIC_GROUP_HEADER, id,
                 MQTT_TWIN_TOPIC, MQTT_STATE_TOPIC_SET))
    
#============================================================================
# Get a grp result topic
# e.g. GRP/name/TWIN/RES
#============================================================================
def getTwinGroupResult(id: str):
    return ("%s/%s/%s/%s"%(MQTT_TOPIC_GROUP_HEADER, id,
                 MQTT_TWIN_TOPIC, MQTT_STATE_TOPIC_RESULT))
 
#============================================================================
# Check to see if the wild mqtt topic definition matches the specific one
# wild: str of topic which may include wildcards eg GRP/#
# fill: specific topic. e.g. GRP/all/TPC/PING
# returns bool of if match
#============================================================================
def topicEquals(wild: str, fill: str):
    w = wild.split("/")
    f = fill.split("/")
    for i in range(len(w)):
        if (i < len(f)):
            if (w[i] == "#"):
                return True
            if (w[i] != "+"):
                if (w[i] != f[i]):
                    return False
    return True
    