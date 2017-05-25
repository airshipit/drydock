# Introspection #

Introspection is a cloud-init compatible metadata service
that is used to make a node self-aware. After a full
deployment by the node driver, the newly installed OS
will contact the introspection API to gain a package of
declaritive data defining the node's role in the site and
enough initial data to start the promenade process of
Kubernetes assimilation