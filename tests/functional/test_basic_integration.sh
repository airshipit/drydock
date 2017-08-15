#/bin/bash

set -x

# Check that we are root
if [[ $(whoami) != "root" ]]
then
  echo "Must be root to run $0"
  exit -1
fi

# Install docker
apt -qq update
apt -y install docker.io jq

# Setup environmental variables
# with stable defaults

# Network
export CEPH_CLUSTER_NET=${CEPH_CLUSTER_NET:-"NA"}
export CEPH_PUBLIC_NET=${CEPH_PUBLIC_NET:-"NA"}
export GENESIS_NODE_IP=${GENESIS_NODE_IP:-"NA"}
export DRYDOCK_NODE_IP=${DRYDOCK_NODE_IP:-${GENESIS_NODE_IP}}
export DRYDOCK_NODE_PORT=${DRYDOCK_NODE_PORT:-31000}
export MAAS_NODE_IP=${MAAS_NODE_IP:-${GENESIS_NODE_IP}}
export MAAS_NODE_PORT=${MAAS_NODE_PORT:-31900}
export MASTER_NODE_IP=${MASTER_NODE_IP:-"NA"}
export NODE_NET_IFACE=${NODE_NET_IFACE:-"eth0"}
export PROXY_ADDRESS=${PROXY_ADDRESS:-"http://one.proxy.att.com:8080"}
export PROXY_ENABLED=${PROXY_ENABLED:-"false"}

# Hostnames
export GENESIS_NODE_NAME=${GENESIS_NODE_NAME:-"node1"}
export MASTER_NODE_NAME=${MASTER_NODE_NAME:-"node2"}

# Charts
export CEPH_CHART_REPO=${CEPH_CHART_REPO:-"https://github.com/openstack/openstack-helm"}
export CEPH_CHART_BRANCH=${CEPH_CHART_BRANCH:-"master"}
export DRYDOCK_CHART_REPO=${DRYDOCK_CHART_REPO:-"https://github.com/att-comdev/aic-helm"}
export DRYDOCK_CHART_BRANCH=${DRYDOCK_CHART_BRANCH:-"master"}
export MAAS_CHART_REPO=${MAAS_CHART_REPO:-"https://github.com/openstack/openstack-helm-addons"}
export MAAS_CHART_BRANCH=${MAAS_CHART_BRANCH:-"master"}

# Images
export DRYDOCK_IMAGE=${DRYDOCK_IMAGE:-"quay.io/attcomdev/drydock:0.2.0-a1"}
export ARMADA_IMAGE=${ARMADA_IMAGE:-"quay.io/attcomdev/armada:v0.6.0"}
export PROMENADE_IMAGE=${PROMENADE_IMAGE:-"quay.io/attcomdev/promenade:master"}

# Filenames
export ARMADA_CONFIG=${ARMADA_CONFIG:-"armada.yaml"}
export PROMENADE_CONFIG=${PROMENADE_CONFIG:-"promenade.yaml"}
export UP_SCRIPT_FILE=${UP_SCRIPT_FILE:-"up.sh"}

# Validate environment
if [[ $GENESIS_NODE_IP == "NA" || $MASTER_NODE_IP == "NA" ]]
then
  echo "GENESIS_NODE_IP and MASTER_NODE_IP env vars must be set to correct IP addresses."
  exit -1
fi

if [[ $CEPH_CLUSTER_NET == "NA" || $CEPH_PUBLIC_NET == "NA" ]]
then
  echo "CEPH_CLUSTER_NET and CEPH_PUBLIC_NET en vars must be set to correct IP subnet CIDRs."
  exit -1
fi

# Required inputs
#   Promenade input-config.yaml
#   Armada Manifest for integrated UCP services

cat promenade.yaml.sub | envsubst > ${PROMENADE_CONFIG}
cat armada.yaml.sub | envsubst > ${ARMADA_CONFIG}
rm -rf configs
mkdir configs

# Generate Promenade configuration
docker run -t -v $(pwd):/target ${PROMENADE_IMAGE} promenade generate -c /target/${PROMENADE_CONFIG} -o /target/configs

# Do Promenade genesis process
cd configs
sudo bash ${UP_SCRIPT_FILE} ./${GENESIS_NODE_NAME}.yaml
cd ..

# Setup kubeconfig
mkdir ~/.kube
cp -r /etc/kubernetes/admin/pki ~/.kube/pki
cat /etc/kubernetes/admin/kubeconfig.yaml | sed -e 's/\/etc\/kubernetes\/admin/./' > ~/.kube/config

# Polling to ensure genesis is complete
while [[ -z $(kubectl get pods -n kube-system | grep 'kube-dns' | grep -e '3/3') ]]
do
  sleep 5
done

# Squash Kubernetes RBAC to be compatible w/ OSH
kubectl update -f ./rbac-generous-permissions.yaml

# Do Armada deployment of UCP integrated services
docker run -t -v ~/.kube:/root/.kube -v $(pwd):/target --net=host \
  ${ARMADA_IMAGE} apply --debug-logging /target/${ARMADA_CONFIG} --tiller-host=${GENESIS_NODE_IP} --tiller-port=44134

# Polling for UCP service deployment

while [[ -z $(kubectl get pods -n ucp | grep drydock | grep Running) ]]
do
  sleep 5
done

# Run Gabbi tests
TOKEN=$(docker run --rm --net=host -e 'OS_AUTH_URL=http://keystone-api.ucp.svc.cluster.local:80/v3' -e 'OS_PASSWORD=password' -e 'OS_PROJECT_DOMAIN_NAME=default' -e 'OS_PROJECT_NAME=service' -e 'OS_REGION_NAME=RegionOne' -e 'OS_USERNAME=drydock' -e 'OS_USER_DOMAIN_NAME=default' -e 'OS_IDENTITY_API_VERSION=3' kolla/ubuntu-source-keystone:3.0.3 openstack token issue -f shell | grep ^id | cut -d'=' -f2 | tr -d '"')

DESIGN_ID=$(docker run  --rm --net=host -e "DD_TOKEN=$TOKEN" -e "DD_URL=http://drydock-api.ucp.svc.cluster.local:9000" -e "LC_ALL=C.UTF-8" -e "LANG=C.UTF-8" --entrypoint /usr/local/bin/drydock $DRYDOCK_IMAGE design create)

TASK_ID=$(docker run  --rm --net=host -e "DD_TOKEN=$TOKEN" -e "DD_URL=http://drydock-api.ucp.svc.cluster.local:9000" -e "LC_ALL=C.UTF-8" -e "LANG=C.UTF-8" --entrypoint /usr/local/bin/drydock $DRYDOCK_IMAGE task create -d $DESIGN_ID -a verify_site)

sleep 15

TASK_STATUS=$(docker run --rm --net=host -e "DD_TOKEN=$TOKEN" -e "DD_URL=http://drydock-api.ucp.svc.cluster.local:9000" -e "LC_ALL=C.UTF-8" -e "LANG=C.UTF-8" --entrypoint /usr/local/bin/drydock $DRYDOCK_IMAGE task show -t $TASK_ID | tr "'" '"'  | sed -e 's/None/null/g')

if [[ $(echo $TASK_STATUS | jq -r .result) == "success" ]]
then
  echo "Action verify_site successful."
  exit 0
else
  echo "Action verify_site failed."
  echo $TASK_STATUS
  exit -1
fi
