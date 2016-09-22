#!/usr/bin/python

import salt.client
import salt.config

import logging
from os.path import dirname
from subprocess import check_output
import yaml

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
    Run a job
    """

    __opts__ = salt.config.client_config('/etc/salt/master')
    bench_dir = ''
    for ext in __opts__['ext_pillar']:
        if 'stack' in ext:
            # TODO only add benchmark.cfg here. Salt returns either a string
            # (when there is on ext_module) or an array :(
            # This needs a better solution...works only if benchmark.cfg is 2nd
            # entry in ext_modules
            bench_dir = dirname(ext['stack'][1])
    default_collection = {}
    with open('{}/collections/default.yml'.format(bench_dir), 'r') as yml:
        try:
            default_collection = yaml.load(yml)
        except YAMLError as error:
            print('Error parsing default collection:')
            print(error)
            exit(1)


    for job in default_collection['jobs']:
        # TODO render configuration into its template and run the job
        print(job)

    # fio = Fio()
    #
    # output = fio.run('foo')
    #
    # return output
