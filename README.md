# helm_drydock
A python REST orchestrator to translate a YAML host topology to a provisioned set of hosts and provide a set of cloud-init post-provisioning instructions.

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

### Server Driver ### 

aka maasdriver

Pluggable provisioner for server bootstrapping. Initial implementation is MaaS client.

### Introspection API ###

aka introspection

API for bootstrapping nodes to load self data. Possibly pluggable as this is basically an
authenticated bridge to the Design State API