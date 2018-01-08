.. _validatedesign:

Validate Design
===============

The DryDock Validation API is a set of logic checks that must be passed before any information from the YAMLs will be
processed by Drydock. These checks are performed synchronously and will return a message list with a success or
failures for each check.

Formatting
----------

This document can be POSTed to the Drydock validatedesign to validate a set of documents that have been
processed by Deckhand::

    {
      rel : "design",
      href: "deckhand+https://{{deckhand_url}}/revisions/{{revision_id}}/rendered-documents",
      type: "application/x-yaml"
    }

v1.0
----

Validation Checks
^^^^^^^^^^^^^^^^^

These checks are meant to check the business logic of documents sent to the validatedesign API.

.. autoclass:: drydock_provisioner.orchestrator.validations.validator.Validator
  :members:
