# Control #

This is the external facing API service to control the rest
of Drydock and query Drydock-managed data.

Anticipate basing this service on the falcon Python library

## Endpoints ##

### /tasks ###

POST - Create a new orchestration task and submit it for execution
GET - Get status of a task
DELETE - Cancel execution of a task if permitted
