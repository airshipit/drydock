=======================
Authoring Site Topology
=======================

Drydock uses a YAML-formatted site topology definition to configure
downstream drivers to provision baremetal nodes. This topology describes
the networking configuration of a site as well as the set of node configurations
that will be deployed. A node configuration consists of network attachment,
network addressing, local storage, kernel selection and configuration and
metadata.

The best source for a sample of the YAML schema for a topology is the unit
test input source_ /tests/yaml_samples/fullsite.yaml in tests/yaml_samples/fullsite.yaml.

Defining Node Storage
=====================

Storage can be defined in the `storage` stanza of either a HostProfile or BaremetalNode
document. The storage configuration can describe creation of partitions on physical disks,
the assignment of physical disks and/or partitions to volume groups, and the creation of
logical volumes. Drydock will make a best effort to parse out system-level storage such
as the root filesystem or boot filesystem and take appropriate steps to configure them in
the active node provisioning driver.

Example YAML schema of the `storage` stanza::

    storage:
      physical_devices:
        sda:
          labels:
            bootdrive: true
          partitions:
            - name: 'root'
              size: '10g'
              bootable: true
              filesystem:
                mountpoint: '/'
                fstype: 'ext4'
                mount_options: 'defaults'
            - name: 'boot'
              size: '1g'
              filesystem:
                mountpoint: '/boot'
                fstype: 'ext4'
                mount_options: 'defaults'
        sdb:
          volume_group: 'log_vg'
      volume_groups:
        log_vg:
          logical_volumes:
            - name: 'log_lv'
              size: '500m'
              filesystem:
                mountpoint: '/var/log'
                fstype: 'xfs'
                mount_options: 'defaults'

Schema
------

The `storage` stanza can contain two top level keys: `physical_devices` and
`volume_groups`. The latter is optional.

Physical Devices and Partitions
-------------------------------

A physical device can either be carved up in partitions (including a single partition
consuming the entire device) or added to a volume group as a physical volume. Each
key in the `physical_devices` mapping represents a device on a node. The key should either
be a device alias defined in the HardwareProfile or the name of the device published
by the OS. The value of each key must be a mapping with the following keys

* `labels`: A mapping of key/value strings providing generic labels for the device
* `partitions`: A sequence of mappings listing the partitions to be created on the device.
The mapping is described below. Incompatible with the `volume_group` specification.
* `volume_group`: A volume group name to add the device to as a physical volume. Incompatible
with the `partitions` specification.

Partition
~~~~~~~~~

A partition mapping describes a GPT partition on a physical disk. It can left as a raw
block device or formatted and mounted as a filesystem

* `name`: Metadata describing the partition in the topology
* `size`: The size of the partition. See the *Size Format* section below
* `bootable`: Boolean whether this partition should be the bootable device
* `part_uuid`: A UUID4 formatted UUID to assign to the partition. If not specified one will be generated
* `filesystem`: A optional mapping describing how the partition should be formatted and mounted
    * `mountpoint`: Where the filesystem should be mounted. If not specified the partition will be left as a raw deice
    * `fstype`: The format of the filesyste. Defaults to ext4
    * `mount_options`: fstab style mount options. Default is 'defaults'
    * `fs_uuid`: A UUID4 formatted UUID to assign to the filesystem. If not specified one will be generated
    * `fs_label`: A filesystem label to assign to the filesystem. Optional.

Size Format
~~~~~~~~~~~

The size specification for a partition or logical volume is formed from three parts

* The first character can optionally be `>` indicating that the size specified is a minimum and the
calculated size should be at least the minimum and should take the rest of the available space on
the physical device or volume group.
* The second part is the numeric portion and must be an integer
* The third part is a label
    * `m`\|`M`\|`mb`\|`MB`: Megabytes or 10^6 * the numeric
    * `g`\|`G`\|`gb`\|`GB`: Gigabytes or 10^9 * the numeric
    * `t`\|`T`\|`tb`\|`TB`: Terabytes or 10^12 * the numeric
    * `%`: The percentage of total device or volume group space

Volume Groups and Logical Volumes
---------------------------------

Logical volumes can be used to create RAID-0 volumes spanning multiple physical disks or partitions.
Each key in the `volume_groups` mapping is a name assigned to a volume group. This name must be specified
as the `volume_group` attribute on one or more physical devices or partitions, or the configuration is invalid.
Each mapping value is another mapping describing the volume group.

* `vg_uuid`: A UUID4 format uuid applied to the volume group. If not specified, one is generated
* `logical_volumes`: A sequence of mappings listing the logical volumes to be created in the volume group

Logical Volume
~~~~~~~~~~~~~~

A logical volume is a RAID-0 volume. Using logical volumes for `/` and `/boot` is supported

* `name`: Required field. Used as the logical volume name.
* `size`: The logical volume size. See *Size Format* above for details.
* `lv_uuid`: A UUID4 format uuid applied to the logical volume: If not specified, one is generated
* `filesystem`: A mapping specifying how the logical volume should be formatted and mounted. See the
*Partition* section above for filesystem details.

