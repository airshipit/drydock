#!/bin/bash
set -x

DRYDOCK_IMAGE="${IMAGE_PREFIX}/${DRYDOCK_IMAGE_NAME}:${IMAGE_TAG}"

function start_db {
    if [[ ! -z $(docker ps | grep 'psql_integration') ]]
    then
      sudo docker stop 'psql_integration'
    fi

    docker run --rm -dp 5432:5432 --name 'psql_integration' postgres:9.5
    sleep 15

    docker run --rm --net host postgres:9.5 psql -h localhost -c "create user drydock with password 'drydock';" postgres postgres
    docker run --rm --net host postgres:9.5 psql -h localhost -c "create database drydock;" postgres postgres
}

function customize_conf {
    default_conffile=$1
    custom_conffile=$2

    DRYDOCK_DB_URL=$(echo ${DRYDOCK_DB_URL} | sed -e 's/[\/&]/\\&/g')
    sed -e "s/^#database_connect_string = <None>/database_connect_string = ${DRYDOCK_DB_URL}/" \
      $default_conffile > $custom_conffile
}

function generate_conf {
    tox -e genconfig > /dev/null
    tox -e genpolicy > /dev/null
    ETCDIR=$(mktemp -d)/drydock
    mkdir -p ${ETCDIR} > /dev/null
    cp etc/drydock/noauth-api-paste.ini ${ETCDIR}/api-paste.ini
    customize_conf etc/drydock/drydock.conf.sample ${ETCDIR}/drydock.conf
    cp etc/drydock/policy.yaml.sample ${ETCDIR}/policy.yaml
    echo ${ETCDIR}
}

function init_db {
    docker run --rm -t --net=host \
      -e DRYDOCK_DB_URL="${DRYDOCK_DB_URL}" \
      --entrypoint /usr/local/bin/alembic \
      ${DRYDOCK_IMAGE} \
      upgrade head
}

function test_drydock {
    TMPETC=$1
    docker run \
      -d --name 'drydock_test' --net host \
      -v ${TMPETC}:/etc/drydock \
      ${DRYDOCK_IMAGE}

    sleep 10

    RESULT=$(curl --noproxy '*' -i 'http://127.0.0.1:9000/api/v1.0/tasks' | tr '\r' '\n' | head -1)
    GOOD="HTTP/1.1 200 OK"
    if [[ ${RESULT} == ${GOOD} ]]
    then
      RC=0
    else
      RC=1
    fi

    docker logs drydock_test
    return $RC
}

function cleanup {
    TMPDIR=$1
    docker stop psql_integration
    docker stop drydock_test
    docker rm drydock_test
#    rm -rf $TMPDIR
}

start_db
export DRYDOCK_DB_URL="postgresql+psycopg2://drydock:drydock@localhost:5432/drydock"
init_db

TMPETC=$(generate_conf)

test_drydock $TMPETC
RC=$?

cleanup $TMPETC

exit $RC
