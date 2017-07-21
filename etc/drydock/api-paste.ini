[app:drydock-api]
paste.app_factory = drydock_provisioner.drydock:paste_start_drydock

[pipeline:main]
pipeline = authtoken drydock-api

[filter:authtoken]
paste.filter_factory = keystonemiddleware.auth_token:filter_factory
