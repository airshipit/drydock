# aic-kube MaaS Orchestration #

## Inventory/Design Schema ##

Would be nice to see this get out of Git-managed flat-files and into
an API accessible datastore that allows more fine-grained queries
and supports inheritance/composition natively

### Requirements ###

1. Use profile inheritance to minimize data repitition
2. Future-proof to support configuration items (CIs) we consider static today
3. Support composition to allow federated source of truth

### Components ###

#### bootstrap_seed.yaml ####

Probably needs renamed, but I see this as being the Formation data
that specifies explicit values - hostnames, IP address assignments,
VLAN IDs, etc...

#### bootstrap_hwdefinition.yaml ####

Looks to be mainly focused on initial OOB control and getting a server
into PXE mode. Should be able to leave as-is and adopt existing
Apollo logic for IPMI.

#### bootstrap_profiles.yaml ####

Currently doesn't exist, but I think it makes sense to separate the
data that describes the design (like general profiles) from the data
that ties the design to explicit assignments (i.e. Formation data)

### Questions/Issues ###

* Need DNS specs in YAML - where to include it, possibly per network
making it effective when that network is chosen as "primary"
	* Can set comma-delimited list of DNS servers per subnet
* Consider YAML pointers and anchors to diminish how much inheritance
has to be calculated in code
	* Does not appear to support key subtraction
	* No way to merge hashes based on a 'primary' key
	* Scott thinks best to keep with managing inheritance in code. Can minimize
	magic via comments in YAML
* Best way of specifying hardware paths (eth0 may not be consistent across boots)
	* PCI bus address
		* For NIC lshw should tie a PCI address to a MAC (serial number) and logical
		name (eth0)
		* MaaS API is keyed to logical name
	* SCSI bus address
* How to specify custom hardware drivers
	* OOB config - /etc/maas/drivers.yaml specify the suite of drivers available
	to MaaS outside what is built into the streams. MaaS will automatically
	consume a driver when it detects hardware that needs it. This config is not
	API accessible.
* Expound on storage, at least specifying primary boot drive

## Orchestrator Service Fabric ##

Consider Go over Python considering performance differences, concurrency support
and ease of deploying static binaries.

### Requirements ###

1. Make interfaces at both ends pluggable
2. Support metadata API for node introspection
3. Support future addition of network and storage orchestration

### Services ###

#### Design Consumer ####

Pluggable service to ingest a inventory/design specification, convert it to a standard
internal representaion, and persist it to the Design State API. Initial implementation
is the consumer of AIC YAML schema.

#### Design State API ####

API for querying and updating the current design specification and persisted orchestration status.
CRUD support of CIs that are not bootstrap-related, but can be used by other automation.

#### Control API ####

User-approachable API for initiating orchestration actions or accessing other internal
APIs

#### Infrastructure Orchestrator ####

Handle validation of complete design, ordering and managing downstream API calls for hardware
provisioning/bootstrapping

#### Server Driver ####

Pluggable provisioner for server bootstrapping. Initial implementation is MaaS client.

#### Network Driver ####

Pluggable provisioner for network provisioning. Initial implementation is Noop.

#### Introspection API ####

API for bootstrapping nodes to load self data. Possibly pluggable as this is basically an
authenticated bridge to the Design State API

### Questions ###

1. Should this drive the MaaS configuration or only drive node deployment?
2. What do we need commissioning scripts for?
	* Firmware updates
	* Hardware RAID configs
	* Hardware manifest validation (as designed/as built)
3. 

## Resources ##

* [MaaS Node Deployment](https://insights.ubuntu.com/2016/01/23/maas-setup-deploying-openstack-on-maas-1-9-with-juju/)
* [MaaS Network Provisioning](https://insights.ubuntu.com/2016/01/31/nodes-networking-deploying-openstack-on-maas-1-9-with-juju/)
* [Custom Curtin Scripts](http://caribou.kamikamamak.com/2015/06/26/custom-partitioning-with-maas-and-curtin-2/)
* [curtin_userdata for bootstrapping K8](https://gist.github.com/aric49/4d424929346e7fbb3ddbd87c7a49ba67)
* [YAML anchors and pointers](http://blog.daemonl.com/2016/02/yaml.html)
* [YAML Wikipedia](https://en.wikipedia.org/wiki/YAML)
* [MaaS 3rd Party Drivers](http://people.canonical.com/~jlane/third-party-drivers.html)
* [MaaS API Spec](https://maas.ubuntu.com/docs2.0/api.html)
* [VMware Go IPMI](https://github.com/vmware/goipmi)


