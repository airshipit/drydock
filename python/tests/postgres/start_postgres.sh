#!/bin/bash
set -x
IMAGE="${DOCKER_REGISTRY}/${IMAGE_PREFIX}/${IMAGE_NAME}:${IMAGE_TAG}-${DISTRO}"
env

if [[ ! -z $(docker ps | grep 'psql_integration') ]]
then
  sudo docker stop 'psql_integration'
fi

IMAGE=${IMAGE:-"quay.io/airshipit/drydock:latest-ubuntu_focal"}

if [[ ! -z $(docker ps | grep 'psql_integration') ]]
then
  sudo docker stop 'psql_integration'
fi

sudo docker run --rm -d -p 5432:5432/tcp -e POSTGRES_HOST_AUTH_METHOD=trust  -e POSTGRES_PASSWORD=postgres --name 'psql_integration' postgres:14.6
sleep 15

docker run --rm --net host postgres:14.6 psql -h localhost -c "create user drydock with password 'drydock';" postgres postgres
docker run --rm --net host postgres:14.6 psql -h localhost -c "create database drydock;" postgres postgres

export DRYDOCK_DB_URL="postgresql+psycopg2://drydock:drydock@localhost:5432/drydock"

sudo docker run --rm -t --net=host -e DRYDOCK_DB_URL="$DRYDOCK_DB_URL" -w /tmp/drydock --entrypoint /usr/local/bin/alembic $IMAGE  upgrade head
