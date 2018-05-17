# Drivers #

Drivers are downstream actors that Drydock will use to actually execute
orchestration actions. It is intended to be a pluggable architecture
so that various downstream automation can be used. A driver must implement all actions even if the implementation is effectively a no-op.

## oob ##

The oob drivers will interface with physical servers' out-of-band
management system (e.g. Dell iDRAC, HP iLO, etc...). OOB management
will be used for setting a system to use PXE boot and power cycling
servers.

### Actions ###

* ConfigNodePxe - Where available, configure PXE boot options (e.g. PXE interface)
* SetNodeBoot - Set boot source (PXE, hard disk) of a node
* PowerOffNode - Power down a node
* PowerOnNode - Power up a node
* PowerCycleNode - Power cycle a node
* InterrogateOob - Interrogate a node's OOB interface. Resultant data is dependent on what functionality is implemented for a particular OOB interface

## node ##

The node drivers will interface with an external bootstrapping system
for loading the base OS on a server and configuring hardware, network,
and storage.

### Actions ###

* CreateNetworkTemplate - Configure site-wide network information in bootstrapper
* CreateStorageTemplate - Configure site-wide storage information in bootstrapper
* CreateBootMedia - Ensure all needed boot media is available to the bootstrapper including external repositories
* PrepareHardwareConfig - Prepare the bootstrapper to handle all hardware configuration actions (firmware updates, RAID configuration, driver installation)
* IdentifyNode - Correlate a node definition in the Drydock internal model with a node detected by the downstream node bootstrapper.
* ConfigureHardware - Update and validate all hardware configurations on a node prior to deploying the OS on it
* InterrogateNode - Interrogate the bootstrapper about node information. Depending on the current state of the node, this interrogation will produce different information.
* ApplyNodeNetworking - Configure networking for a node
* ApplyNodeStorage - Configure storage for a node
* ApplyNodePlatform - Configure stream and kernel options for a node
* DeployNode - Deploy the OS to a node
* DestroyNode - Take steps to bring a node back to a blank undeployed state

## network ##

The network drivers will interface with switches for managing port
configuration to support the bootstrapping of physical nodes. This is not
intended to be a network provisioner, but instead is a support driver
for node bootstrapping where temporary changes to network configurations
are required.

### Actions ###

* InterrogatePort - Request information about the current configuration of a network port
* ConfigurePortProvisioning - Configure a network port in provisioning (PXE) mode
* ConfigurePortProduction - Configure a network port in production (configuration post-deployment) mode
