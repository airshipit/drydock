# Control #

This is the external facing API service to control the rest
of Drydock and query Drydock-managed data.

Anticipate basing this service on the falcon Python library

## Endpoints ##

### /tasks ###

POST - Create a new orchestration task and submit it for execution
GET - Get status of a task
DELETE - Cancel execution of a task if permitted

### /designs ###

POST - Create a new site design so design parts can be added
GET - Get a current design if available

### /designs/{id}/parts

POST - Submit a new design part to be ingested and added to this design
GET - View a currently defined design part
PUT - Replace an existing design part