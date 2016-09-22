#!/usr/bin/python

import salt.client

from subprocess import check_output
import logging

log = logging.getLogger(__name__)
local_client = salt.client.LocalClient()

class Fio(object):

    def __init__(self):
        clients = local_client.cmd('I@roles:cephs-client and I@cluster:ceph',
                'pillar.get', ['public_address'], expr_form='compound')
        self.cmd_args = ['fio']

        self.cmd_args.extend(['--client={}'.format(client) for client in clients])

    def run(self, job):
        output = check_ouput(self.cmd_args + [job])

        return output


def run(**kwargs):
    """
    Run a fio job
    """
    fio = Fio()

    output = fio.run('foo')

    return output
