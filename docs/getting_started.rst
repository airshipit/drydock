=======================================
Installing Drydock in a Dev Environment
=======================================

Drydock runs in Python 3.x only and is tested on Ubuntu 16.04 standard
images. It is recommended that your development environment be a Ubuntu
16.04 virtual machine.

MaaS
----

Drydock requires a downstream node provisioning service and currently
the only driver implemented is for Canonical MaaS. So to begin with
install MaaS following their instructions_ https://docs.ubuntu.com/maas/2.2/en/installconfig-package-install.
The MaaS region and rack controllers can be installed in the same VM
as Drydock or a separate VM.

On the VM that MaaS is installed on, create an admin user:

::

    $ sudo maas createadmin --username=admin --email=admin@example.com

You can now access the MaaS UI by pointing a browser at http://maas_vm_ip:5240/MAAS
and follow the configuration journey_ https://docs.ubuntu.com/maas/2.2/en/installconfig-webui-conf-journey
to finish getting MaaS ready for use.

Drydock Configuration
---------------------

Clone the git repo and customize your configuration file

::

    git clone https://github.com/att-comdev/drydock
    mkdir /tmp/drydock-etc
    cp drydock/examples/drydock.conf /tmp/drydock-etc/
    cp -r drydock/examples/bootdata /tmp/drydock-etc/

In `/tmp/drydock-etc/drydock.conf` customize your maas_api_url to be
the URL you used when opening the web UI and maas_api_key.

When starting the Drydock container, /tmp/drydock-etc will be
mounted as /etc/drydock with your customized configuration.

Drydock
-------

Drydock is easily installed via the Docker image at quay.io/attcomdev/drydock:latest.
You will need to customize and mount your configuration file

::

    $ sudo docker run -v /tmp/drydock-etc:/etc/drydock -P -d drydock:latest

Configure Site
--------------

To use Drydock for site configuration, you must craft and load a site topology
YAML. An example of this is in examples/designparts_v1.0.yaml.

Load Site
---------

Use the Drydock CLI create a design and load the configuration

::

    $ drydock --token <token> --url <drydock_url> design create
    $ drydock --token <token> --url <drydock_url> part create -d <design_id> -f <yaml_file>

Use the CLI to create tasks to deploy your site

::

    $ drydock --token <token> --url <drydock_url> task create -d <design_id> -a verify_site
    $ drydock --token <token> --url <drydock_url> task create -d <design_id> -a prepare_site
    $ drydock --token <token> --url <drydock_url> task create -d <design_id> -a prepare_node
    $ drydock --token <token> --url <drydock_url> task create -d <design_id> -a deploy_node

