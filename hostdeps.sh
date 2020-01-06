#!/bin/bash

# Install host-level package dependencies
# needed for local testing
set -x

if [[ ! -z $(uname -a | grep Ubuntu) ]]
then
  apt-get update
  installed_pkgs=$(dpkg --get-selections | awk '!/deinstall/ { gsub(/:.*/,"",$1); print $1 }')
  set -a added_pkgs
  for reqfile in $(ls requirements-host*.txt)
  do
    for l in $(grep -vE '(^ *#)|(^$)' "${reqfile}")
    do
      # Do extra magic to support a list of alternative packages separated by '|'
      # none of the packages are found, install the first one listed
      IFS='|' read -a pkgalts <<< "${l}"
      pkgfound=0
      for a in "${pkgalts[@]}"
      do
        if grep -qE "^${a}$" <<< "${installed_pkgs}"
        then
          pkgfound=1
          break
        fi
      done
      if [[ "${pkgfound}" -eq 0 ]]
      then
        added_pkgs+=("${pkgalts[0]}")
      fi
    done
  done
  if [[ ${#added_pkgs[@]} -gt 0 ]]
  then
    DEBIAN_FRONTEND=noninteractive apt-get \
      -o Dpkg::Options::="--force-confdef" \
      -o Dpkg::Options::="--force-confold" \
      install -y --no-install-recommends "${added_pkgs[@]}"
  fi
else
  echo "Only support testing on Ubuntu hosts at this time."
fi
