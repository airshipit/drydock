# Drydock Model #

Object models for the drydock design parts and subparts. We use oslo.versionedobjects as the supporting library for object management
to support RPC and versioned persistence.

## Features ##

### Inheritance ###

Drydock supports inheritance in the design data model.

Currently this only supports BaremetalNode inheriting from HostProfile and
HostProfile inheriting from HostProfile.

Inheritance rules:

1. A child overrides a parent for part and subpart attributes
2. For attributes that are lists, the parent list and child list
are merged.
3. A child can remove a list member by prefixing the value with '!'
4. For lists of subparts (i.e. HostInterface and HostPartition) if
there is a member in the parent list and child list with the same name
(as defined by the get_name() method), the child member inherits from
the parent member. The '!' prefix applies here for deleting a member
based on the name.

### Phased Data ###

The *source* of the data in a object instance can be one of three
types.

* Designed - This is data directly ingested by Drydock representing a design part (Site, HostProfile, etc...) supplied by an external source
* Compiled - This is designed data that has been processed through the Drydock
inheritance / merge system. It is the effective design that will be implemented.
* Build - This is the result of actual implementation. It should basically match the compiled view of the model, but might have some additional information only available after implementation.