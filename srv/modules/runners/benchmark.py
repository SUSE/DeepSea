#!/usr/bin/python

import salt.client
import salt.config

import logging
from jinja2 import Environment, FileSystemLoader
from os.path import dirname
from subprocess import check_output
import yaml

log = logging.getLogger(__name__)
local_client = salt.client.LocalClient()

class Fio(object):

    def __init__(self, bench_dir, work_dir):
        clients = local_client.cmd('I@roles:cephs-client and I@cluster:ceph',
                'pillar.get', ['public_address'], expr_form='compound')
        self.cmd_args = ['fio']

        self.cmd_args.extend(['--client={}'.format(client) for client in clients])

        self.bench_dir = bench_dir
        self.work_dir = work_dir

        self.jinja_env = Environment(loader=FileSystemLoader('{}/{}'.format(bench_dir,
            'templates')))

    def run(self, job):
        output = check_ouput(self.cmd_args + [job])

        return output

    def parse_job(self, job_spec):
        job = self._get_parameters(job_spec)
        # which template does the job want

        template = self.jinja_env.get_template(job['template'])

        self._populate_and_write(template, job)

    def _populate_and_write(self, template, job):

        # render template and save job file
        template.stream(job).dump('{}/jobfile'.format(self.work_dir))

    def _get_parameters(self, job_spec):
        with open('{}/{}'.format(self.bench_dir, job_spec, 'r')) as yml:
            try:
                job = yaml.load(yml)
            except YAMLError as error:
                print('Error parsing job spec in file {}/templates/{}'.format(self.bench_dir, job_spec))
                print(error)
                exit(1)
        job.update({'dir': self.work_dir})
        return job


def run(**kwargs):
    """
    Run a job
    """

    # extract kwargs
    work_dir = ''
    if 'work_dir' in kwargs:
        work_dir = kwargs['work_dir']
        print('work dir is {}'.format(work_dir))
    else:
        return 1



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

    fio = Fio(bench_dir, work_dir)

    print(default_collection)
    for job_spec in default_collection['jobs']:
        # TODO render configuration into its template and run the job
        print(job_spec)
        print(type(job_spec))
        fio.parse_job(job_spec)
    #
    # output = fio.run('foo')
    #
    # return output
