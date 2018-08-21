#!/bin/bash
set -x

UBUNTU_REPO=${UBUNTU_REPO:-""}
TRUSTED_UBUNTU_REPO=${TRUSTED_UBUNTU_REPO:-"no"}
ALLOW_UNATHENTICATED=${ALLOW_UNAUTHENTICATED:-"false"}
PIP_INDEX_URL=${PIP_INDEX_URL:-""}
PIP_TRUSTED_HOST=${PIP_TRUSTED_HOST:-""}

ADDL_BUILD_ARGS=""

if [[ ! -z "${UBUNTU_REPO}" ]]
then
  ADDL_BUILD_ARGS="${ADDL_BUILD_ARGS} --build-arg UBUNTU_REPO=${UBUNTU_REPO}"
  ADDL_BUILD_ARGS="${ADDL_BUILD_ARGS} --build-arg TRUSTED_UBUNTU_REPO=${TRUSTED_UBUNTU_REPO}"
  ADDL_BUILD_ARGS="${ADDL_BUILD_ARGS} --build-arg ALLOW_UNAUTHENTICATED=${ALLOW_UNAUTHENTICATED}"
fi

if [[ ! -z "${PIP_INDEX_URL}" ]]
then
  ADDL_BUILD_ARGS="${ADDL_BUILD_ARGS}| --build-arg PIP_INDEX_URL=${PIP_INDEX_URL}"
  ADDL_BUILD_ARGS="${ADDL_BUILD_ARGS}| --build-arg PIP_TRUSTED_HOST=${PIP_TRUSTED_HOST}"
fi

docker build --network host -t ${IMAGE} --label ${LABEL} -f images/drydock/Dockerfile \
  ${ADDL_BUILD_ARGS} \
  --build-arg BUILD_DIR=${BUILD_DIR} \
  --build-arg http_proxy=${http_proxy} \
  --build-arg https_proxy=${https_proxy} \
  --build-arg HTTP_PROXY=${HTTP_PROXY} \
  --build-arg HTTPS_PROXY=${HTTPS_PROXY} \
  --build-arg no_proxy=${no_proxy} \
  --build-arg NO_PROXY=${NO_PROXY} .

