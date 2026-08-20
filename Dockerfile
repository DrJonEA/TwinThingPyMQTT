#Docker file to run TwinMgr within Docker
#Env required:
# MQTT_USER
# MQTT_PASSWD
# MQTT_HOST
# MQTT_PORT
# MQTT_CERT
# TWIN_DB_USER
# TWIN_DB_PASSWD
# TWIN_DB_HOST
# TWIN_DB_PORT
# TWIN_DB_SCHEMA

FROM python:3.12-slim

# copy over our requirements.txt file
COPY src/requirements.txt /tmp/

# upgrade pip and install required python packages
RUN pip3 install -U pip
RUN pip3 install -r /tmp/requirements.txt

# copy over our app code
COPY ./src/ /src
COPY ./libs/ /libs

ENV PYTHONPATH=/src:/libs/twinThing/py

CMD ["python3","/src/mainTwinMgr.py"]

