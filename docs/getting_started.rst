=======================================
Installing Drydock in a Dev Environment
=======================================

Bootstrap Kubernetes
--------------------

You can bootstrap your Helm-enabled Kubernetes cluster via the Openstack-Helm
AIO_ http://openstack-helm.readthedocs.io/en/latest/install/developer/all-in-one.html
process or using the UCP Promenade_ https://github.com/att-comdev/promenade tool.

Deploy Drydock and Dependencies
-------------------------------

Drydock is most easily deployed using Armada to deploy the Drydock
container into a Kubernetes cluster via Helm charts. The Drydock chart
is in aic-helm_ https://github.com/att-comdev/aic-helm. It depends on
the deployments of the MaaS_ https://github.com/openstack/openstack-helm-addons chart
and the Keystone_ https://github.com/openstack/openstack-helm chart.

A integrated deployment of these charts can be accomplished using the
Armada_ https://github.com/att-comdev/armada tool. An example integration
chart can be found in the UCP integrations_ https://github.com/att-comdev/ucp-integration
repo in the manifests/basic_ucp directory.

::
    $ git clone https://github.com/att-comdev/ucp-integration
    $ sudo docker run -ti -v $(pwd):/target -v ~/.kube:/armaada/.kube quay.io/attcomdev/armada:master apply --tiller-host <host_ip> --tiller-port 44134 /target/manifests/basic_ucp/ucp-armada.yaml
    $ # wait for all pods in kubectl get pods -n ucp are 'Running'
    $ KS_POD=$(kubectl get pods -n ucp | grep keystone | cut -d' ' -f1)
    $ TOKEN=$(docker run --rm --net=host -e 'OS_AUTH_URL=http://keystone-api.ucp.svc.cluster.local:80/v3' -e 'OS_PASSWORD=password' -e 'OS_PROJECT_DOMAIN_NAME=default' -e 'OS_PROJECT_NAME=service' -e 'OS_REGION_NAME=RegionOne' -e 'OS_USERNAME=drydock' -e 'OS_USER_DOMAIN_NAME=default' -e 'OS_IDENTITY_API_VERSION=3' kolla/ubuntu-source-keystone:3.0.3 openstack token issue -f shell | grep ^id | cut -d'=' -f2 | tr -d '"')
    $ docker run  --rm -ti --net=host -e "DD_TOKEN=$TOKEN" -e "DD_URL=http://drydock-api.ucp.svc.cluster.local:9000" -e "LC_ALL=C.UTF-8" -e "LANG=C.UTF-8" $DRYDOCK_IMAGE /bin/bash


                                     Load Site
---------

To use Drydock for site configuration, you must craft and load a site topology
YAML. An example of this is in examples/designparts_v1.0.yaml.

Documentation on building your topology document is under construction

Use the Drydock CLI create a design and load the configuration

::

    # drydock design create
    # drydock part create -d <design_id> -f <yaml_file>

Use the CLI to create tasks to deploy your site

::

    # drydock task create -d <design_id> -a verify_site
    # drydock task create -d <design_id> -a prepare_site
    # drydock task create -d <design_id> -a prepare_node
    # drydock task create -d <design_id> -a deploy_node

A demo of this process is available at https://asciinema.org/a/133906
