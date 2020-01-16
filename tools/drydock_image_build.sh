#!/bin/bash
set -x

UBUNTU_BASE_IMAGE=${UBUNTU_BASE_IMAGE:-""}
UBUNTU_REPO=${UBUNTU_REPO:-""}
DISTRO=${DISTRO:-"ubuntu_bionic"}
TRUSTED_UBUNTU_REPO=${TRUSTED_UBUNTU_REPO:-"no"}
ALLOW_UNATHENTICATED=${ALLOW_UNAUTHENTICATED:-"false"}
PIP_INDEX_URL=${PIP_INDEX_URL:-""}
PIP_TRUSTED_HOST=${PIP_TRUSTED_HOST:-""}

ADDL_BUILD_ARGS=""

if [[ ! -z "${UBUNTU_BASE_IMAGE}" ]]
then
  ADDL_BUILD_ARGS="${ADDL_BUILD_ARGS} --build-arg FROM=${UBUNTU_BASE_IMAGE}"
fi

if [[ ! -z "${UBUNTU_REPO}" ]]
then
  ADDL_BUILD_ARGS="${ADDL_BUILD_ARGS} --build-arg UBUNTU_REPO=${UBUNTU_REPO}"
  ADDL_BUILD_ARGS="${ADDL_BUILD_ARGS} --build-arg TRUSTED_UBUNTU_REPO=${TRUSTED_UBUNTU_REPO}"
  ADDL_BUILD_ARGS="${ADDL_BUILD_ARGS} --build-arg ALLOW_UNAUTHENTICATED=${ALLOW_UNAUTHENTICATED}"
fi

if [[ ! -z "${PIP_INDEX_URL}" ]]
then
  ADDL_BUILD_ARGS="${ADDL_BUILD_ARGS} --build-arg PIP_INDEX_URL=${PIP_INDEX_URL}"
  ADDL_BUILD_ARGS="${ADDL_BUILD_ARGS} --build-arg PIP_TRUSTED_HOST=${PIP_TRUSTED_HOST}"
fi

PROXY_ARGS=""
if [[ "${USE_PROXY}" == true ]]; then
  PROXY_ARGS="--build-arg http_proxy=${PROXY} \
    --build-arg https_proxy=${PROXY} \
    --build-arg HTTP_PROXY=${PROXY} \
    --build-arg HTTPS_PROXY=${PROXY} \
    --build-arg no_proxy=${NO_PROXY} \
    --build-arg NO_PROXY=${NO_PROXY}"
fi

docker build --network host -t ${IMAGE} --label ${LABEL} \
  --label org.opencontainers.image.revision=${COMMIT} \
  --label org.opencontainers.image.created="$(date --rfc-3339=seconds --utc)" \
  --label org.opencontainers.image.title=${IMAGE_NAME} \
  -f "images/drydock/Dockerfile.${DISTRO}" \
  --build-arg BUILD_DIR=${BUILD_DIR} \
  ${PROXY_ARGS} \
  ${ADDL_BUILD_ARGS} .