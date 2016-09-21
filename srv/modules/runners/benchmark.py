#!/usr/bin/python

import salt.client

from subprocess import check_output
import logging

log = logging.getLogger(__name__)

def run(**kwargs):
    """
    Run a fio job
    """
    job_file = ''
    if 'job' in kwargs:
        job_file = kwargs['job']
    else:
        return [ False ]

    local = salt.client.LocalClient()

    clients = local.cmd('I@roles:cephs-client and I@cluster:ceph', 'pillar.get',
            ['public_address'], expr_form='compound')

    fio_args = ''
    # TODO: this only works with one client host sofar...will need to pass all args as array
    for client in clients:
        fio_args = '{}--client={}'.format(fio_args, clients[client])

    output = check_output(['fio', fio_args, job_file])

    return output
