# Statemgmt #

Statemgmt is the interface to the persistence store
for holding site design data as well as build status data

/drydock - Base namespace for drydock data

## As Designed ##

Serialization of Drydock internal model as ingested. Not externally writable.

/drydock/design
/drydock/design/base - The base site design used for the first deployment
/drydock/design/[changeID] - A change layer on top of the base site design. Chrono ordered

## As Built ##

Serialization of Drydock internal model as rendered to effective implementation including build status. Not externally writable.

/drydock/build
/drydock/build/[datestamp] - A point-in-time view of what was deployed with deployment results

## Tasks ##

Management of task state for the internal orchestrator

/drydock/tasks

## Node data ##

Per-node data that can drive introspection as well as accept updates from nodes

/drydock/nodedata
/drydock/nodedata/[nodename] - Per-node data, can be seeded with Ingested metadata but can be updated during by orchestrator or node

## Service data ##

Per-service data (may not be needed)

/drydock/servicedata
/drydock/servicedata/[servicename]

## Global data ##

Generic k:v store that can be produced/consumed by non-Drydock services via the Drydock API

/drydock/globaldata