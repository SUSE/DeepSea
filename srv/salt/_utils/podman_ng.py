# -*- coding: utf-8 -*-
'''
Management of Podman Containers

:depends: Podman

.. note::
    This is a quick and dirty solution for management of Podman containers.

    Podman support is not yet available from SaltStack:
        https://github.com/saltstack/salt/issues/50624

    Likewise, the Python bindings for Podman are not yet packaged for SLE15:
        https://github.com/docker/docker-py

    This solution should be replaced when the above upstream components
    become available downstream.
'''

__docformat__ = 'restructuredtext en'

import functools
import logging
import salt.utils.path
import salt.config
import salt.loader
import salt.modules.pillar
import rs

from salt.exceptions import CommandExecutionError

PODMAN_BIN = salt.utils.path.which('podman')

# Set up logging
log = logging.getLogger(__name__)


class Podman(object):
    def __init__(self, pillar):
        self.cmd = [PODMAN_BIN, 'run', '--rm', '--net=host']
        self.pillar = pillar
        self.host()
        self.image()

    def image(self):
        self.container_image = self.pillar.get('container_image', None)
        if not self.container_image:
            raise CommandExecutionError(
                "Container image not set - check `salt-call pillar.get container_image`"
            )

    def host(self):
        __opts__ = salt.config.minion_config('/etc/salt/minion')
        __grains__ = salt.loader.grains(__opts__)

        self.node_name = __grains__.get('host', None)
        if not self.node_name:
            raise CommandExecutionError(
                "Grains 'host' is empty - check `salt-call grains.get host`")

    def env(self, setting):
        self.cmd += ["-e", setting]
        return self

    def vol(self, volume):
        self.cmd += ["-v", volume]
        return self

    def entrypoint(self, points):
        self.cmd += ["--entrypoint"] + points
        return self

    def args(self, arguments):
        self.cmd += arguments
        self.command = ' '.join([x.strip() for x in self.cmd])
