# Overview
[![Travis](https://travis-ci.org/hunt-genes/interface-slurm-cluster.svg?branch=master)](https://travis-ci.org/hunt-genes/interface-slurm-cluster)
[![license](https://img.shields.io/github/license/hunt-genes/interface-slurm-cluster.svg)](./copyright)

This interface provides handles the communication between the Slurm controller and nodes.

# Usage

## Requires
This interface will set the following states:

* `slurm-cluster.connected` The relation is established, but the Slurm controller has not provided the Slurm configuration yet. Here you can send the node info to the controller so it can build the cluster configuration.

```python
@when('slurm-cluster.joined')
def set_node_info(cluster):
    cluster.send_node_info()
```

* `slurm-cluster.available` The Slurm controller has provided the Slurm configuration. You can now setup the node with the cluster configuration.

```python
@when('slurm-cluster.available')
def configure_node(cluster):
    controller_config = cluster.get_config()
    if data_changed('slurm-config', controller_config):
        # Do something with the config
```

## Provides

This interface will set the following states:

* `slurm-cluster.available` The Slurm nodes have provided their info. You can now build the cluster configuration and send it to nodes.

```python
@when('slurm-cluster.available')
def configure_controller(cluster):
    nodes = cluster.get_nodes()
    partitions = cluster.get_partitions()
    if data_changed('nodes', nodes):
        # Do something with nodes and partitions
        # cluster_config = {
            ###
        # }
        # Send complete cluster configuration to nodes
        cluster.send_controller_config(cluster_config)
```