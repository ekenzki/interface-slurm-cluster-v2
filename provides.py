from collections import defaultdict

from charmhelpers.core.hookenv import atexit
from charmhelpers.core.hookenv import relation_get
from charmhelpers.core.hookenv import related_units
from charmhelpers.contrib.templating.contexts import dict_keys_without_hyphens

from charms.reactive import RelationBase
from charms.reactive import hook
from charms.reactive import scopes
from charms.reactive.helpers import data_changed


class SlurmProvides(RelationBase):
    scope = scopes.GLOBAL

    @hook('{provides:slurm-cluster}-relation-{joined,changed}')
    def changed(self):
        self._update_states()

    @hook('{provides:slurm-cluster}-relation-{departed,broken}')
    def departed(self):
        self._update_states()

    def _update_states(self):
        if self._nodes_ready():
            if self.get_nodes():
                self.set_state('{relation_name}.available')
                if data_changed('nodes', self.get_nodes()):
                    self.set_state('{relation_name}.changed')
                    atexit(
                        lambda: self.remove_state('{relation_name}.changed'))
        else:
            self.remove_state('{relation_name}.available')

    def _nodes_ready(self):
        """Return True if all remote units have a private address."""
        return self._get_remote_all(keys=['private-address'])

    def get_nodes(self):
        """Return a list of dictionaries with info for each node."""
        return self._get_remote_all(
            keys=['hostname', 'private-address', 'partition'])

    def get_partitions(self):
        """Return the partitions and their nodes as a dictionary.

        :return: Dictionary with partitions as keys and list of nodes as
            values.
        :rtype: dict

        Example::

            >>> print(get_partitions())
            {
                'partition1': ['node1', 'node2', 'node3'],
                'partition2': ['node4']
            }

        """
        # Use defaultdict(list) so we can append items to the the values
        partitions_dict = defaultdict(list)
        for node in self.get_nodes():
            partitions_dict[node['partition']].append(node['hostname'])
        return dict(partitions_dict)

    def _get_remote_all(self, keys):
        """Return a list of dictionaries of values presented by remote units.

        :param list keys: The list of keys to retrieve from all remote units.
        :return: List of dictionaries with all values from all remote units.
        :rtype: list

        Example::

            >>> print(_get_remote_all(keys=['hostname']))
            [
                { 'hostname': 'host1' },
                { 'hostname': 'host2' }
            ]

        """
        values = []
        for conversation in self.conversations():
            for relation_id in conversation.relation_ids:
                for unit in related_units(relation_id):
                    remote_dict = {}
                    for key in keys:
                        remote_dict[key] = relation_get(key, unit, relation_id)
                    values.append(dict_keys_without_hyphens(remote_dict))
        return values

    def send_controller_config(self, config):
        self.set_remote(data={
            'config': config,
        })
