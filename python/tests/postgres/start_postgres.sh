#!/bin/bash
set -x

DOCKER_REGISTRY=${DOCKER_REGISTRY:-"quay.io"}
IMAGE_PREFIX=${IMAGE_PREFIX:-"airshipit"}
IMAGE_NAME=${IMAGE_NAME:-"drydock"}
IMAGE_TAG=${IMAGE_TAG:-"latest"}
DISTRO=${DISTRO:-"ubuntu_focal"}


IMAGE="${DOCKER_REGISTRY}/${IMAGE_PREFIX}/${IMAGE_NAME}:${IMAGE_TAG}-${DISTRO}"

if [[ ! -z $(docker ps | grep 'psql_integration') ]]
then
  docker stop 'psql_integration'
fi



if [[ ! -z $(docker ps | grep 'psql_integration') ]]
then
  docker stop 'psql_integration'
fi

docker run --rm -dp 5432:5432 --name 'psql_integration' -e POSTGRES_HOST_AUTH_METHOD=trust quay.io/airshipit/postgres:14.8
sleep 15

docker run --rm --net host quay.io/airshipit/postgres:14.8 psql -h localhost -c "create user drydock with password 'drydock';" postgres postgres
docker run --rm --net host quay.io/airshipit/postgres:14.8 psql -h localhost -c "create database drydock;" postgres postgres

export DRYDOCK_DB_URL="postgresql+psycopg2://drydock:drydock@localhost:5432/drydock"

docker run --rm -t --net=host -e DRYDOCK_DB_URL="$DRYDOCK_DB_URL" -w /tmp/drydock --entrypoint /usr/local/bin/alembic $IMAGE  upgrade head
