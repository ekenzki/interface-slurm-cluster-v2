import charms.reactive.flags as flags
import charms.reactive as reactive
import charms.reactive.helpers as helpers

from charmhelpers.core.hookenv import (
    DEBUG,
    log,
)

class SlurmRequires(reactive.Endpoint):

    def _controller_relation(self):
        # can only be related to a single controller
        assert len(self.relations) < 2
        return self.relations[0]

    @property
    def ingress_address(self):
        return self._controller_relation().to_publish['ingress-address']

    def send_node_info(self, hostname, partition, default):
        # can only handle a single controller relation both active and
        # standby receive the same node info for this relation
        rel = self._controller_relation()
        rel.to_publish.update({
            'hostname': hostname,
            'partition': partition,
            'default': default,
        })

    def _controller_config_ready(self, config):
        '''Returns True if we find this node in the controller config.
        '''
        if config:
            log('Determining readiness by config: {}'.format(config))
            for node in config.get('nodes'):
                if node['ingress_address'] == self.ingress_address:
                    log('The controller is ready')
                    return True
        else:
            log('The controller is NOT ready')
            return False

    @reactive.when('endpoint.{endpoint_name}.changed')
    def controllers_changed(self):
        """Assess active-backup controllers and set the appropriate
        flags based on the result. Relation data for both controllers
        is relevant as address and hostname information is taken for
        a backup controller as well. Changed active and backup
        .changed events are processed in properties - layers need to
        handle active and backup config changed events in a single
        handler"""
        self._active_data = self._controller_config()

        if self._controller_config_ready(self._active_data):
            flags.set_flag(self.expand_name(
                'endpoint.{endpoint_name}.active.available'))
            flags.set_flag(self.expand_name(
                'endpoint.{endpoint_name}.active.changed'))
            # TODO: JSON is not serializable => need to either remove
            # this and execute more or solve the problem
            #if helpers.data_changed('active_data', self._active_data):
            #    flags.set_flag(self.expand_name(
            #        'endpoint.{endpoint_name}.active.changed'))

        # processed the relation changed event - can clear this flag now
        flags.clear_flag(self.expand_name('changed'))

    @property
    def active_data(self):
        return self._active_data

    def _controller_config(self):
        rel = self._controller_relation()

        partitions = None
        for u in rel.joined_units:
            recv = u.received
            log('Received from {}: {}'.format(u.unit_name, recv))
            # the expectation is that backup controller units will not
            # post any config and there will only be one config posted
            # by the active controller
            cpartitions = recv.get('partitions')
            if partitions and cpartitions:
                # catch a split-brain condition when two controllers
                # advertise possibly conflicting config data which means
                # that active controller change 
                # TODO: error/status handling for this
                flags.set_flag(self.expand_name(
                    'endpoint.{endpoint_name}.split-brain'))
            else:
                partitions = cpartitions
        return recv if partitions else {}
