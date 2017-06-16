# Orchestrator #

The orchestrator is the core of drydock and will manage
the ordering of driver actions to implement the main Drydock
actions. Each of these actions will be started by the
external cLCP orchestrator with different parameters to
control the scope of the action.

Orchestrator should persist the state of each task
such that on failure the task can retried and only the
steps needed will be executed.

## Drydock Tasks ##

Bullet points listed below are not exhaustive and will
change as we move through testing

### ValidateDesign ###

Load design data from the statemgmt persistent store and
validate that the current state of design data represents
a valid site design. No claim is made that the design data
is compatible with the physical state of the site.

#### Validations ####

* All baremetal nodes have an address, either static or DHCP, for all networks they are attached to.
* No static IP assignments are duplicated
* No static IP assignments are outside of the network they are targetted for
* All IP assignments are within declared ranges on the network
* Networks assigned to each node's interface are within the set of of the attached link's allowed_networks
* Boot drive is above minimum size

### VerifySite ###

Verify site-wide resources are in a useful state

* Driver downstream resources are reachable (e.g. MaaS)
* OS images needed for bootstrapping are available
* Promenade or other next-step services are up and available
* Verify credentials are available

### PrepareSite ###

Begin preparing site-wide resources for bootstrapping. This
action will lock site design data for changes.

* Configure bootstrapper with site network configs
* Shuffle images so they are correctly configured for bootstrapping

### VerifyNode ###

Verification of per-node configurations within the context
of the current node status

* Status: Present
    * Basic hardware verification as available via OOB driver
        - BIOS firmware
        - PCI layout
        - Drives
        - Hardware alarms
    * IPMI connectivity
* Status: Prepared
    - Full hardware manifest
    - Possibly network connectivity
    - Firmware versions

### PrepareNode ###

Prepare a node for bootstrapping

* Configure network port for PXE
* Configure a node for PXE boot
* Power-cycle the node
* Setup commissioning configuration
    - Hardware drivers
    - Hardware configuration (e.g. RAID)
* Configure node networking
* Configure node storage
* Interrogate node
    - lshw output
    - lldp output

### DeployNode ###

Begin bootstrapping the node and monitor
success

* Initialize the Introspection service for the node
* Bootstrap the node (i.e. Write persistent OS install)
* Ensure network port is returned to production configuration
* Reboot node from local disk
* Monitor platform bootstrapping

### DestroyNode ###

Destroy current node configuration and rebootstrap from scratch

## Integration with Drivers ##

Based on the requested task and the current known state of a node
the orchestrator will call the enabled downstream drivers with one
or more tasks. Each call will provide the driver with the desired
state (the applied model) and current known state (the build model).