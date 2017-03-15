# Ingester #

Ingester is a pluggable consumer of site design data. It
will support consuming data in different formats from
different sources.

Each ingester plugin should be able source data
based on user-provided parameters and parse that data
into the Drydock internal model (helm_drydock.model).

Each plugin does not need to support every type of design
data as a single site design may be federated from multiple
sources.