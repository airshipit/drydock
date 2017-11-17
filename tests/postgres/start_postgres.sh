#!/bin/bash
set -x
DRYDOCK_IMAGE="${IMAGE_PREFIX}/${DRYDOCK_IMAGE_NAME}:${IMAGE_TAG}"

if [[ ! -z $(docker ps | grep 'psql_integration') ]]
then
  sudo docker stop 'psql_integration'
fi

DRYDOCK_IMAGE=${DRYDOCK_IMAGE:-"drydock:latest"}

if [[ ! -z $(docker ps | grep 'psql_integration') ]]
then
  sudo docker stop 'psql_integration'
fi

sudo docker run --rm -dp 5432:5432 --name 'psql_integration' postgres:9.5
sleep 15

docker run --rm --net host postgres:9.5 psql -h localhost -c "create user drydock with password 'drydock';" postgres postgres
docker run --rm --net host postgres:9.5 psql -h localhost -c "create database drydock;" postgres postgres

export DRYDOCK_DB_URL="postgresql+psycopg2://drydock:drydock@localhost:5432/drydock"

sudo docker run --rm -t --net=host -e DRYDOCK_DB_URL="$DRYDOCK_DB_URL" --entrypoint /usr/local/bin/alembic $DRYDOCK_IMAGE upgrade head
