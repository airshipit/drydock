#!/bin/bash

# Install golang-go package, and build the baclient library
set -x

if $(uname -a | grep -q Ubuntu); then
  GOPATH=$1
  BUILD_DIR=$2
  if [[ ! -f ./baclient_built ]]; then
    GO111MODULE=off GOPATH=${GOPATH} go build -v -o ${BUILD_DIR}/baclient baclient
  else
    echo "Baclient library is already built. No action."
  fi
else
  echo "Only support testing on Ubuntu hosts at this time."
fi

