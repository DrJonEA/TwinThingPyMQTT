# TwinThingPyMQTT

TwinThing Python framework for MQTT, plus TwinMgr for managing a central
digital twin.

## Framework

This Python MQTT framework produces IoT clients that follow the same specification
as the C++ library for Raspberry Pi Pico, [TwinThingsPico1-2W](https://github.com/DrJonEA/twinThingPico1-2W).

Clients operate as IoT devices with state and use a standard set of topics to report,
request, and set state.

## TwinMgr
TwinMgr uses the framework to provide a local digital twin of a device. Clients can
operate through the digital twin rather than communicating directly with the device.
The twin holds state while the device is unavailable and updates the device when it
becomes available.

TwinMgr can also operate on devices in a group, including retrieving all group state
or setting particular attributes on all devices in the group.

# Dependencies

- Python 3
- Python packages listed in `src/requirements.txt`
- MySQL database
- [EMQX](https://www.emqx.io/) with MySQL authentication and authorization
- [twinThing](https://github.com/jondurrant/twinThing)

# File Structure

- `src/` - application and library files
- `src/mainTwinMgr.py` - main program for TwinMgr
- `example/` - simple examples of stateful IoT clients
- `exp/` - experimental code
- `libs/` - non-PyPI packages used by the code, including TwinThing
- `test/` - test scripts that interact with TwinMgr
- `ddl/` - MySQL table definitions


# Deployment - TwinMgr

The included `Dockerfile` builds TwinMgr as a Docker image.

TwinMgr expects the following environment variables:

- `MQTT_USER` - MQTT username and client ID
- `MQTT_PASSWD` - MQTT password
- `MQTT_HOST` - MQTT broker hostname
- `MQTT_PORT` - MQTT broker port, normally 1883 or 8883
- `MQTT_CERT` - CA certificate chain used to validate the broker when TLS is enabled
- `TWIN_DB_USER` - Database username for the Twin and EMQX tables
- `TWIN_DB_PASSWD` - Database password
- `TWIN_DB_HOST` - Database hostname
- `TWIN_DB_PORT` - Database port
- `TWIN_DB_SCHEMA` - Database schema containing the Twin and EMQX tables

The Docker Compose deployment passes these values from the generated root `.env` file.
Ensure the CA certificate is mounted into the container when `MQTT_CERT` is used.


# MQTT Server

The framework can work with any MQTT broker, but TwinMgr is currently specific to
EMQX using MySQL authentication and authorization. It relies on topic ACLs to
control access to device and group topics.

## Topic Structure
The topic structure is summarized below.

- `TNG/<ID>/` - device namespace; in this example, `<ID>` is also the MQTT username
- `TNG/<ID>/LC` - lifecycle events that announce connection and disconnection
- `TNG/<ID>/TPC` - messaging topics for a specific device

For example, if a Pico is named `pico`:

- `TNG/pico/TPC/PING` - ping request sent to Pico
- `TNG/pico/TPC/PONG` - pong response to the ping

Group topics use the following structure:

- `GRP/<Group>/TPC/` - topics for communicating with a group of devices

For example:

- `GRP/ALL/TPC/PING` - a ping topic to which all IoT devices listen

TwinMgr adds these topics for an individual device:

- `TNG/<ID>/TWIN/GET` - get twin state
- `TNG/<ID>/TWIN/SET` - set twin state
- `TNG/<ID>/TWIN/UPD` - report twin state, including desired, reported, and declined state and metadata
- `TNG/<ID>/TWIN/RES` - return a query response when query syntax is used with `GET`

Group twin topics are:

- `GRP/<GRP>/TWIN/GET` - get group state using the group query syntax
- `GRP/<GRP>/TWIN/SET` - set group state using the group query syntax
- `GRP/<GRP>/TWIN/RES` - return group query results

See `test/things/` for examples that exercise these topic APIs.

## Log Topic

Services publish operational log messages to the shared group log topic:

- `GRP/ALL/TPC/LOG` - service status and diagnostic messages

The Test Monitor publishes a JSON payload with this structure:

```json
{
	"source": "healthcheck-monitor",
	"service": "oracIoTHub.monitor",
	"sourceTS": 1715789478,
	"level": "info",
	"msg": "Passed: 5 | Skipped: 1 | Failed: 0",
	"detail": "[]"
}
```

Field definitions:

- `source` - MQTT client ID that generated the message
- `service` - logical service name
- `sourceTS` - Unix timestamp in seconds when the message was generated
- `level` - log severity, such as `info`, `warning`, or `error`
- `msg` - human-readable summary
- `detail` - JSON-encoded details; for the Test Monitor, this contains the failed test names

## Clients
You must configure users and permissions for your clients.

The default policy should deny everything unless explicitly allowed. With EMQX 6
and the MySQL authorizer, the existing `mqtt_acl` table is mapped as follows:

- `allow = 0` -> `deny`
- `allow = 1` -> `allow`
- `access = 1` -> `subscribe`
- `access = 2` -> `publish`
- `access = 3` -> `all`

Avoid relying on a database catch-all `deny #` row when using `EMQX_AUTHORIZATION__NO_MATCH=deny`;
the broker configuration already supplies the default deny policy.

Legacy rule representation:

```json
{
	  "topic": "#",
	  "action": "pubsub",
	  "access": "deny"
}
```

An individual device requires permissions similar to:

```json
[
	{
	  "topic": "GRP/ALL/TPC/#",
	  "action": "sub",
	  "access": "allow"
	},
	{
	  "topic": "TNG/$CLIENTID/#",
	  "action": "pubsub",
	  "access": "allow"
	}
]
```

To give a device access to a group called `saber`:

```json
[
	{
	  "topic": "GRP/saber/TPC/#",
	  "action": "pubsub",
	  "access": "allow"
	}
]
```

TwinMgr requires permissions to publish and subscribe to device topics and to
operate the TWIN channels under both device and group hierarchies:

```json
[
	{
	  "topic": "GRP/+/TWIN/#",
	  "action": "pubsub",
	  "access": "allow"
	},
	{
	  "topic": "TNG/+/STATE/UPD",
	  "action": "sub",
	  "access": "allow"
	},
	{
	  "topic": "TNG/+/TWIN/#",
	  "action": "pubsub",
	  "access": "allow"
	}
]
```

The exact MySQL ACL rows must also cover the lifecycle subscription filters used
by TwinMgr, such as `TNG/+/LC/#`, and any group topics it publishes or subscribes to.




