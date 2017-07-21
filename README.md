# drydock_provisioner

A python REST orchestrator to translate a YAML host topology to a provisioned set of hosts and provide a set of cloud-init post-provisioning instructions.

To build and run, first move into the root directory of the repo and run:

    $ tox -e genconfig
    $ tox -e genpolicy
    $ sudo docker build . -t drydock
    $ vi etc/drydock/drydock.conf # Customize configuration
    $ sudo docker run -d -v $(pwd)/etc/drydock:/etc/drydock -P --name='drydock' drydock
    $ DDPORT=$(sudo docker port drydock 8000/tcp | awk -F ':' '{ print $NF }')
    $ curl -v http://localhost:${DDPORT}/api/v1.0/designs

See [Configuring Drydock](docs/configuration.rst) for details on customizing the configuration. To be useful, Drydock needs
to operate in a realistic topology and has some required downstream services.

* A VM running Canonical MaaS v2.2+
* A functional Openstack Keystone instance w/ the v3 API
* Docker running to start the Drydock image (can be co-located on the MaaS VM)
* A second VM or Baremetal Node to provision via Drydock
    * Baremetal needs to be able to PXE boot
    * Preferrably Baremetal will have an IPMI OOB interface
    * Either VM or Baremetal will need to have one interface on the same L2 network (LAN or VLAN) as the MaaS VM

See the [Getting Started](docs/getting_started.rst) guide  for instructions.

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
