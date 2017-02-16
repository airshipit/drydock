# drydock
A python REST orchestrator to translate a YAML host topology to a provisioned set of hosts and provide a set of cloud-init post-provisioning instructions.

## Modular service

### Design Consumer ###

Pluggable service to ingest a inventory/design specification, convert it to a standard
internal representaion, and persist it to the Design State API. Initial implementation
is the consumer of AIC YAML schema.

### Design State API ###

API for querying and updating the current design specification and persisted orchestration status.
CRUD support of CIs that are not bootstrap-related, but can be used by other automation.

### Control API ###

User-approachable API for initiating orchestration actions or accessing other internal
APIs

### Infrastructure Orchestrator ###

Handle validation of complete design, ordering and managing downstream API calls for hardware
provisioning/bootstrapping

### Server Driver ###

Pluggable provisioner for server bootstrapping. Initial implementation is MaaS client.

### Network Driver ###

Pluggable provisioner for network provisioning. Initial implementation is Noop.

### Introspection API ###

API for bootstrapping nodes to load self data. Possibly pluggable as this is basically an
authenticated bridge to the Design State API