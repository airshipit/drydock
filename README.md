# drydock_provisioner

A python REST orchestrator to translate a YAML host topology to a provisioned
set of hosts and provide a set of post-provisioning instructions.

See full documentation at [https://airship-drydock.readthedocs.io/](https://airship-drydock.readthedocs.io/).

## Required

* Python 3.5+
* A running instance of Postgres v9.5+
* A running instance of Openstack Keystone w/ the v3 API enabled
* A running instance of Canonical MaaS v2.3+

## Recommended

* A running Kubernetes cluster with Helm initialized
* Familiarity with the Airship platform suite of services

## Building

This service is intended to be built as a Docker container, not as a
standalone Python package. That being said, instructions are included below
for building as a package and as an image.

### Virtualenv

To build and install Drydock locally in a virtualenv first generate configuration
and policy file templates to be customized

    $ tox -e genconfig
    $ tox -e genpolicy
    $ virtualenv -p python3.5 /var/tmp/drydock
    $ . /var/tmp/drydock/bin/activate
    $ pip install -r requirements-lock.txt
    $ pip install .
    $ cp -r etc/drydock /etc/drydock

### Docker image

    $ docker build . -t drydock

## Running

The preferred deployment pattern of Drydock is via a Helm chart
to deploy Drydock into a Kubernetes cluster. Additionally use of
the rest of the Airship services provides additional functionality
for deploying (Armada) and using (Promenade, Deckhand) Drydock.

You can see an example of a full Airship deployment in the [Airship in a Bottle](https://github.com/openstack/airship-in-a-bottle) repository.

### Stand up Kubernetes

Use the Airship [Promenade](https://github.com/openstack/airship-promenade)
tool for starting a self-hosted Kubernetes cluster with Kubernetes
Helm deployed.

### Deploy Drydock Dependencies

There are Helm charts for deploying all the dependencies of Dryodck.
Use them for preparing your Kuberentes cluster to host Drydock.

* [Postgres](https://github.com/openstack/openstack-helm/tree/master/postgresql)
* [Keystone](https://github.com/openstack/openstack-helm/tree/master/keystone)
* [MAAS](https://github.com/openstack/airship-maas)

### Deploy Drydock

Ideally you will use the Airship [Armada](https://airship-armada.readthedocs.io)
tool for deploying the Drydock chart with proper overrides, but if not you can
use the `helm` CLI tool. The below are overrides needed during deployment

* values.labels.node_selector_key: This is the kubernetes label assigned to the node you expect to host Drydock
* values.conf.dryodck.maasdriver: This is URL Drydock will use to access the MAAS API (including the URL path)
* values.images.drydock: The Drydock docker image to use
* values.images.drydock_db_sync: The Drydock docker image to use
