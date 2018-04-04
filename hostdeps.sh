#!/bin/bash
# Install host-level package dependencies
# needed for local testing
if [[ ! -z $(uname -a | grep Ubuntu) ]]
then
  apt install -y --no-install-recommends $(grep -v '^#' requirements-host.txt)
else
  echo "Only support testing on Ubuntu hosts at this time."
fi
