# Drivers #

Drivers are downstream actors that Drydock will use to actually execute
orchestration actions. It is intended to be a pluggable architecture
so that various downstream automation can be used.

## oob ##

The oob drivers will interface with physical servers' out-of-band
management system (e.g. Dell iDRAC, HP iLO, etc...). OOB management
will be used for setting a system to use PXE boot and power cycling
servers.

## node ##

The node drivers will interface with an external bootstrapping system
for loading the base OS on a server and configuring hardware, network,
and storage.

## network ##

The network drivers will interface with switches for managing port
configuration to support the bootstrapping of physical nodes. This is not
intended to be a network provisioner, but instead is a support driver
for node bootstrapping where temporary changes to network configurations
are required.