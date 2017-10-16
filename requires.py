import yaml

from charmhelpers.core.hookenv import atexit
from charmhelpers.core.hookenv import unit_private_ip

from charms.reactive import RelationBase
from charms.reactive import hook
from charms.reactive import scopes
from charms.reactive.helpers import data_changed


class SlurmRequires(RelationBase):
    scope = scopes.GLOBAL

    @hook('{requires:slurm-cluster}-relation-{joined,changed}')
    def changed(self):
        self.set_state('{relation_name}.connected')
        if self._controller_config_ready():
            self.set_state('{relation_name}.available')
            if data_changed('config', self.get_config()):
                self.set_state('{relation_name}.changed')
                atexit(lambda: self.remove_state('{relation_name}.changed'))
        else:
            self.remove_state('{relation_name}.available')

    @hook('{requires:slurm-cluster}-relation-{departed,broken}')
    def departed(self):
        self.remove_state('{relation_name}.available')
        self.remove_state('{relation_name}.connected')
        self.remove_state('{relation_name}.changed')

    def send_node_info(self, hostname, partition, default):
        self.set_remote(data={
            'hostname': hostname,
            'partition': partition,
            'default': default,
        })

    def get_config(self):
        """Returns the configuration from the controller as a dict."""
        return yaml.safe_load(self.get_remote('config'))

    def _controller_config_ready(self):
        """Returns True if we find this node in the controller config."""
        if self.get_remote('config'):
            config = self.get_config()
            for node in config.get('nodes'):
                if unit_private_ip() in node.values():
                    return True
        else:
            return False
