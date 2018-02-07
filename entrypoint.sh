#!/bin/bash
set -ex

CMD="drydock"
PORT=${PORT:-9000}
# Number of uWSGI workers to handle API requests
DRYDOCK_API_WORKERS=${DRYDOCK_API_WORKERS:-"1"}
# Threads per worker
DRYDOCK_API_THREADS=${DRYDOCK_API_THREADS:-"4"}
# HTTP timeout
HTTP_TIMEOUT=${HTTP_TIMEOUT:-"600"}

if [ "$1" = 'server' ]; then
# Run Drydock under uWSGI
#   --http - Port to listen for requests on
#   --paste - Use DeployPaste for handling requests and use the specified config INI file
#   --enable-threads - Enable the Python GIL so that service can be multithreaded
#   -L - Turn off uWSGI request logging, rely totally on logging within the application
#   --pyargs - Provide some command line arguments to the Python executable
#   --threads - Number of threads each uWSGI worker should use for handling requests
#   --workers - Number of uWSGI workers/processes for handling requests
#   --http-timeout - How long uWSGI will proxy the python code processing before disconnecting a client
    exec uwsgi --http :${PORT} --paste config:/etc/drydock/api-paste.ini --enable-threads -L --pyargv "--config-file /etc/drydock/drydock.conf" --threads $DRYDOCK_API_THREADS --workers $DRYDOCK_API_WORKERS --http-timeout $HTTP_TIMEOUT
fi

exec ${CMD} $@
