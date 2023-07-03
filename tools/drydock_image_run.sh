#!/bin/bash
set -x

IMAGE=${DOCKER_REGISTRY}/${IMAGE_PREFIX}/${IMAGE_NAME}:${IMAGE_TAG}-${DISTRO}
PSQL_CONTAINER_NAME=psql_integration_$(date +%Y%m%d%H%M%s%s)
DRYDOCK_CONTAINER_NAME=drydock_test_$(date +%Y%m%d%H%M%s%s)

function start_db {
    if [[ ! -z $(docker ps | grep "${PSQL_CONTAINER_NAME}" ) ]]
    then
      sudo docker stop "${PSQL_CONTAINER_NAME}"
    fi

    docker run --rm -dp 5432:5432 --name "${PSQL_CONTAINER_NAME}" -e POSTGRES_HOST_AUTH_METHOD=trust postgres:14.8
    sleep 15

    docker run --rm --net host postgres:14.8 psql -h localhost -c "create user drydock with password 'drydock';" postgres postgres
    docker run --rm --net host postgres:14.8 psql -h localhost -c "create database drydock;" postgres postgres
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
      ${IMAGE} \
      upgrade head
}

function test_drydock {
    TMPETC=$1
    docker run \
      -d --name "${DRYDOCK_CONTAINER_NAME}" --net host \
      -v ${TMPETC}:/etc/drydock \
      ${IMAGE}

    sleep 10

    RESULT=$(curl --noproxy '*' -i 'http://127.0.0.1:9000/api/v1.0/tasks' | tr '\r' '\n' | head -1)
    GOOD="HTTP/1.1 200 OK"
    if [[ "${RESULT}" != "${GOOD}" ]]; then
      if docker exec -t ${CONTAINER_NAME} /bin/bash -c "curl -i 'http://127.0.0.1:9000/api/v1.0/tasks' --noproxy '*' | tr '\r' '\n' | head -1 "; then
        RESULT="${GOOD}"
      fi
    fi

    if [[ ${RESULT} == ${GOOD} ]]
    then
      RC=0
    else
      RC=1
    fi

    docker logs "${DRYDOCK_CONTAINER_NAME}"
    return $RC
}

function cleanup {
    TMPDIR=$1
    docker stop "${PSQL_CONTAINER_NAME}"
    docker stop "${DRYDOCK_CONTAINER_NAME}"
    docker rm "${DRYDOCK_CONTAINER_NAME}"
   rm -rf $TMPDIR
}

start_db
export DRYDOCK_DB_URL="postgresql+psycopg2://drydock:drydock@localhost:5432/drydock"
init_db

TMPETC=$(generate_conf)

test_drydock $TMPETC
RC=$?

cleanup $TMPETC

exit $RC
