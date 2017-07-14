# drydock_provisioner
A python REST orchestrator to translate a YAML host topology to a provisioned set of hosts and provide a set of cloud-init post-provisioning instructions.

To run:

    $ docker build . -t drydock
    $ docker run -v /path/to/drydock/repo/examples:/etc/drydock -P --name='drydock' drydock
    $ DDPORT=$(docker ps -f name=drydock | grep -oE '0.0.0.0:[0-9]+' | cut -d':' -f 2)
    $ curl -v http://localhost:${DDPORT}/api/v1.0/designs

## Modular service

### Design Consumer ###

aka ingester

Pluggable service to ingest a inventory/design specification, convert it to a standard
internal representaion, and persist it to the Design State API. Initial implementation
is the consumer of YAML schema.

### Design State API ###

aka statemgmt

API for querying and updating the current design specification and persisted orchestration status.
CRUD support of CIs that are not bootstrap-related, but can be used by other automation.

### Control API ###

aka control

User-approachable API for initiating orchestration actions or accessing other internal
APIs

### Infrastructure Orchestrator ###

aka orchestrator

Handle validation of complete design, ordering and managing downstream API calls for hardware
provisioning/bootstrapping

### OOB Driver ###

Pluggable provider for server OOB (ILO) management

aka driver/oob

### Node Driver ###

aka driver/node

Pluggable provisioner for server bootstrapping. Initial implementation is MaaS client.

### Introspection API ###

aka introspection

API for bootstrapping nodes to load self data. Possibly pluggable as this is basically an
authenticated bridge to the Design State API
