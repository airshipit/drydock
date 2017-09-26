#!/bin/bash

sudo docker run --rm -dp 5432:5432 --name 'psql_integration' postgres:9.5
sleep 15

psql -h localhost -c "create user drydock with password 'drydock';" postgres postgres
psql -h localhost -c "create database drydock;" postgres postgres

export DRYDOCK_DB_URL="postgresql+psycopg2://drydock:drydock@localhost:5432/drydock"
alembic upgrade head

