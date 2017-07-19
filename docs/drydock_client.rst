===========================================================
 drydock_client - client for drydock_provisioner RESTful API
===========================================================

The drydock_client module can be used to access a remote (or local)
Drydock REST API server. It supports tokenized authentication and
marking API calls with an external context marker for log aggregation.

It is composed of two parts - a DrydockSession which denotes the call
context for the API and a DrydockClient which gives access to actual
API calls.

Simple Usage
============

The usage pattern for drydock_client is to build a DrydockSession
with your credentials and the target host. Then use this session
to build a DrydockClient to make one or more API calls. The
DrydockSession will care for TCP connection pooling and header
management::

    import drydock_provisioner.drydock_client.client as client
    import drydock_provisioner.drydock_client.session as session

    dd_session = session.DrydockSession('host.com', port=9000, token='abc123')
    dd_client = client.DrydockClient(dd_session)

    drydock_task = dd_client.get_task('ba44e582-6b26-11e7-81cc-080027ef795a')

Drydock Client Method API
=========================

drydock_client.client.DrydockClient supports the following methods for
accessing the Drydock RESTful API

get_design_ids
--------------

Return a list of UUID-formatted design IDs

get_design
----------

Provide a UUID-formatted design ID, receive back a dictionary representing
a objects.site.SiteDesign instance. You can provide the kwarg 'source' with
the value of 'compiled' to see the site design after inheritance is applied.

create_design
-------------

Create a new design. Optionally provide a new base design (by UUID-formatted
design_id) that the new design uses as the starting state. Receive back a
UUID-formatted string of design_id

get_part
--------

Get the attributes of a particular design part. Provide the design_id the part
is loaded in, the kind (one of 'Region', 'NetworkLink', 'Network', 'HardwareProfile',
'HostProfile' or 'BaremetalNode' and the part key (i.e. name). You can provide the kwarg
'source' with the value of 'compiled' to see the site design after inheritance is
applied.

load_parts
----------

Parse a provided YAML string and load the parts into the provided design context

get_tasks
---------

Get a list of all task ids

get_task
--------

Get the attributes of the task identified by the provided task_id

create_task
-----------

Create a task to execute the provided action on the provided design context
