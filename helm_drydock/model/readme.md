# Drydock Model #

Models for the drydock design parts and subparts

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

In other words, as a modeled object goes from design to apply
to build the model keeps the data separated to retain reference
values and provide context around particular attribute values.

* Design - The data ingested from sources such as Formation
* Apply - Computing inheritance of design data to render an effective site design
* Build - Maintaining actions taken to implement the design and the results

Currently only applies to BaremetalNodes as no other design parts
flow through the build process.