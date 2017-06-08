# Actions requiring admin authority
#"admin_required": "role:admin or is_admin:1"

# Get task status
# GET  /api/v1.0/tasks
# GET  /api/v1.0/tasks/{task_id}
#"physical_provisioner:read_task": "role:admin"

# Create validate_design task
# POST  /api/v1.0/tasks
#"physical_provisioner:validate_design": "role:admin"

# Create verify_site task
# POST  /api/v1.0/tasks
#"physical_provisioner:verify_site": "role:admin"

# Create prepare_site task
# POST  /api/v1.0/tasks
#"physical_provisioner:prepare_site": "role:admin"

# Create verify_node task
# POST  /api/v1.0/tasks
#"physical_provisioner:verify_node": "role:admin"

# Create prepare_node task
# POST  /api/v1.0/tasks
#"physical_provisioner:prepare_node": "role:admin"

# Create deploy_node task
# POST  /api/v1.0/tasks
#"physical_provisioner:deploy_node": "role:admin"

# Create destroy_node task
# POST  /api/v1.0/tasks
#"physical_provisioner:destroy_node": "role:admin"

# Read loaded design data
# GET  /api/v1.0/designs
# GET  /api/v1.0/designs/{design_id}
#"physical_provisioner:read_data": "role:admin"

# Load design data
# POST  /api/v1.0/designs
# POST  /api/v1.0/designs/{design_id}/parts
#"physical_provisioner:ingest_data": "role:admin"

