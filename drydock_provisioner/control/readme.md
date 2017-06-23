# Control #

This is the external facing API service to control the rest
of Drydock and query Drydock-managed data.


## v1.0 Endpoints ##

### /api/v1.0/tasks ###

POST - Create a new orchestration task and submit it for execution
GET - Get status of a task
DELETE - Cancel execution of a task if permitted


### /api/v1.0/designs ###

POST - Create a new site design so design parts can be added

### /api/v1.0/designs/{id}

GET - Get a current design if available. Param 'source=compiled' to calculate the inheritance chain and compile the effective design.

### /api/v1.0/designs/{id}/parts

POST - Submit a new design part to be ingested and added to this design
GET - View a currently defined design part
PUT - Replace an existing design part *Not Implemented*

### /api/v1.0/designs/{id}/parts/{kind}/{name}

GET - View a single design part. param 'source=compiled' to calculate the inheritance chain and compile the effective configuration for the design part.