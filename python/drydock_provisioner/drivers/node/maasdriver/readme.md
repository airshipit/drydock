# MaaS Node Driver #

This driver will handle node provisioning using Ubuntu MaaS 2.1. It expects
the Drydock config to hold a valid MaaS API URL (e.g. http://host:port/MAAS/api/2.0)
and a valid API key for authentication.

## Drydock Model to MaaS Model Relationship ##

### Site ###

Will provide some attributes used for configuring MaaS site-wide such
as tag definitions and repositories.

### Network Link ###

Will provide attributes for configuring Node/Machine interfaces

### Network ###

MaaS will be configured with a single 'space'. Each Network in Drydock
will translate to a unique MaaS fabric+vlan+subnet. Any network with
an address range of type 'dhcp' will cause DHCP to be enabled in MaaS
for that network.

### Hardware Profile ###

A foundation to a Baremetal Node definition. Not directly used in MaaS

### Host Profile ###

A foundation to a Baremetal Node definition. Not directly used in MaaS

### Baremetal Node ###

Defines all the attributes required to commission and deploy nodes via MaaS

* bootdisk fields and partitions list - Define local node storage configuration
to be implemented by MaaS
* addressing and interface list - Combined with referenced network links and networks, define
interface (physical and virtual (bond / vlan)) configurations and network
addressing
* tags and owner data - Statically defined metadata that will propagate to
MaaS
* base_os - Select which stream a node will be deployed with
* kernel and kernel params - Allow for custom kernel selection and parameter
definition
