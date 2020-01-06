#!/bin/bash

# Install golang-go package, and build the baclient library
set -x

if $(uname -a | grep -q Ubuntu); then
  GOPATH=$1
  BUILD_DIR=$2
  if [[ ! -f ./baclient_built ]]; then
    apt-get update
    DEBIAN_FRONTEND=noninteractive apt-get \
      -o Dpkg::Options::="--force-confdef" \
      -o Dpkg::Options::="--force-confold" \
      install -y --no-install-recommends golang-go
    GOPATH=${GOPATH} go build -o ${BUILD_DIR}/baclient baclient
  else
    echo "Baclient library is already built. No action."
  fi
else
  echo "Only support testing on Ubuntu hosts at this time."
fi

