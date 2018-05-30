..
      Copyright 2017 AT&T Intellectual Property.
      All Rights Reserved.

      Licensed under the Apache License, Version 2.0 (the "License"); you may
      not use this file except in compliance with the License. You may obtain
      a copy of the License at

          http://www.apache.org/licenses/LICENSE-2.0

      Unless required by applicable law or agreed to in writing, software
      distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
      WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
      License for the specific language governing permissions and limitations
      under the License.

=======================================
Installing Drydock in a Dev Environment
=======================================

Bootstrap Kubernetes
--------------------

You can bootstrap your Helm-enabled Kubernetes cluster via the Openstack-Helm
`AIO <https://docs.openstack.org/openstack-helm/latest/install/developer/index.html>`_
or the `Promenade <https://airshipit.readthedocs.io/projects/promenade/en/latest/>`_ tools.

Deploy Drydock and Dependencies
-------------------------------

Drydock is most easily deployed using Armada to deploy the Drydock
container into a Kubernetes cluster via Helm charts. The Drydock chart
is in the ``charts/drydock`` directory. It depends on
the deployments of the `MaaS <https://git.openstack.org/cgit/openstack/airship-maas/>`_
chart and the `Keystone <https://git.openstack.org/cgit/openstack/openstack-helm/>`_ chart.

A integrated deployment of these charts can be accomplished using the
`Armada <https://airshipit.readthedocs.io/projects/armada/en/latest/>`_ tool. An example integration
chart can be found in the
`Airship in a Bottle <http://git.openstack.org/cgit/openstack/airship-in-a-bottle/>`_ repo in the
``./manifests/dev_single_node`` directory.

Load Site
---------

To use Drydock for site configuration, you must craft and load a site topology
YAML. An example of this is in ``./test/yaml_samples/deckhand_fullsite.yaml``.

Documentation on building your topology document is at :ref:`topology_label`.

Drydock requires that the YAML topology be hosted somewhere, either the preferred
method of using `Deckhand <https://airshipit.readthedocs.io/projects/deckhand/en/latests/>`_
or through a simple HTTP server like Nginx or Apache.

Use the CLI to create tasks to deploy your site

.. code:: bash

    # drydock task create -d <design_url> -a verify_site
    # drydock task create -d <design_url> -a prepare_site
    # drydock task create -d <design_url> -a prepare_nodes
    # drydock task create -d <design_url> -a deploy_nodes

A demo of this process is available at https://asciinema.org/a/133906
