.. _task:

Tasks
=====

Tasks are requests for Drydock to perform an action asynchronously. Depending on the
action being requested, tasks could take seconds to hours to complete. When a task is
created, a identifier is generated and returned. That identifier can be used to poll
the task API for task status and results.

Task Document Schema
--------------------

This document can be posted to the Drydock :ref:`task-api` to create a new task.::

    {
      "action": "validate_design|verify_site|prepare_site|verify_node|prepare_node|deploy_node|destroy_node",
      "design_ref": "http_uri|deckhand_uri|file_uri",
      "node_filter": {
        "filter_set_type": "intersection|union",
        "filter_set": [
          {
            "filter_type": "intersection|union",
            "node_names": [],
            "node_tags": [],
            "node_labels": {},
            "rack_names": [],
            "rack_labels": {},
          }
        ]
      }
    }

The filter is computed by taking the set of all defined nodes. Each filter in the filter set is applied
by either finding the union or intersection of filtering the full set of nodes by the attribute values
specified. The result set of each filter is then combined as either an intersection or union with that result
being the final set the task is executed against.

Assuming you have a node inventory of::

  [
    {
      "name": "a",
      "labels": {
        "type": "physical",
        "color": "blue"
      }
    },
    {
      "name": "b",
      "labels": {
        "type": "virtual",
        "color": "yellow"
      }
    },
    {
      "name": "c",
      "labels": {
        "type": "physical",
        "color": "yellow"
      }
    }

Example::

    "filter_set": [
      {
        "filter_type": "intersection",
        "node_labels": {
          "color": "yellow",
          "type": "physical"
        }
      },
      {
        "filter_type": "intersection",
        "node_names": ["a"]
      }
    ],
    "filter_set_type": "union"

The above filter set results in a set ``a`` and ``c``.


Task Status Schema
------------------

When querying the state of an existing task, the below document will be returned::

    {
      "Kind": "Task",
      "apiVersion": "v1",
      "task_id": "uuid",
      "action": "validate_design|verify_site|prepare_site|verify_node|prepare_node|deploy_node|destroy_node",
      "design_ref": "http_uri|deckhand_uri|file_uri",
      "parent_task_id": "uuid",
      "subtask_id_list": ["uuid","uuid",...],
      "status": "requested|queued|running|terminating|complete|terminated",
      "node_filter": {
        "filter_set_type": "intersection|union",
        "filter_set": [
          {
            "filter_type": "intersection|union",
            "node_names": [],
            "node_tags": [],
            "node_labels": {},
            "rack_names": [],
            "rack_labels": {},
          }
        ]
      },
      "created": iso8601 UTC timestamp,
      "created_by": "user",
      "updated": iso8601 UTC timestamp,
      "terminated": iso8601 UTC timestamp,
      "terminated_by": "user",
      "result": Status object
    }

The Status object is based on the UCP standardized response format::

    {
      "Kind": "Status",
      "apiVersion": "v1",
      "metadata": {},
      "message": "Drydock Task ...",
      "reason": "Failure reason",
      "status": "failure|success|partial_success|incomplete",
      "details": {
        "errorCount": 0,
        "messageList": [
           StatusMessage
        ]
      }
    }

The StatusMessage object will change based on the context of the message, but will at a minimum
consist of the below::

  {
    "message": "Textual description",
    "error": true|false,
    "context_type": "site|network|node",
    "context": "site_name|network_name|node_name",
    "ts": iso8601 UTC timestamp,
  }


