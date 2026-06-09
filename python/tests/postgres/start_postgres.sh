#!/bin/bash
set -x

echo "DISTRO is set to: $DISTRO"
DOCKER_REGISTRY=${DOCKER_REGISTRY:-"quay.io"}
IMAGE_PREFIX=${IMAGE_PREFIX:-"airshipit"}
IMAGE_NAME=${IMAGE_NAME:-"drydock"}
IMAGE_TAG=${IMAGE_TAG:-"latest"}
DISTRO=${DISTRO:-"ubuntu_jammy"}


IMAGE="${DOCKER_REGISTRY}/${IMAGE_PREFIX}/${IMAGE_NAME}:${IMAGE_TAG}-${DISTRO}"

if docker ps | grep -q 'psql_integration'
then
  docker stop 'psql_integration'
fi

docker run --rm -dp 5432:5432 --name 'psql_integration' -e POSTGRES_HOST_AUTH_METHOD=trust quay.io/airshipit/postgres:17.5
sleep 15

docker run --rm --net host quay.io/airshipit/postgres:17.5 psql -h localhost -c "create user drydock with password 'drydock';" postgres postgres
docker run --rm --net host quay.io/airshipit/postgres:17.5 psql -h localhost -c "create database drydock owner drydock;" postgres postgres

export DRYDOCK_DB_URL="postgresql+psycopg2://drydock:drydock@localhost:5432/drydock"

docker run --rm -t --net=host -e DRYDOCK_DB_URL="$DRYDOCK_DB_URL" -w /tmp/drydock --entrypoint /usr/local/bin/alembic "$IMAGE" upgrade head
