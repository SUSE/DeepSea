#!/usr/bin/python

import salt.client
import salt.config

import logging
from jinja2 import Environment, FileSystemLoader
from os.path import dirname, basename, splitext
from subprocess import check_output
import yaml

log = logging.getLogger(__name__)
local_client = salt.client.LocalClient()

class Fio(object):

    def __init__(self, bench_dir, work_dir, log_dir):
        clients = local_client.cmd('I@roles:mds-client and I@cluster:ceph',
                'pillar.get', ['public_address'], expr_form='compound')
        self.cmd = 'fio'

        self.cmd_args = ['--output-format=json']

        self.client_args = []
        self.client_args.extend(['--client={}'.format(clients[client]) for client in clients])

        self.bench_dir = bench_dir
        self.log_dir = log_dir
        self.work_dir = work_dir

        self.jinja_env = Environment(loader=FileSystemLoader('{}/{}'.format(bench_dir,
            'templates')))

    def run(self, job_spec):
        jobfile = self._parse_job(job_spec)
        '''
        create a list that alternates between --client arguments and job files
        e.g. [--client=host1, jobfile, --client=host2, jobfile]
        fio expects a job file for every remote agent
        '''
        cmd = [None] * 2 * len(self.client_args)
        cmd[::2] = self.client_args
        cmd[1::2] = [jobfile] * len(self.client_args)
        self.cmd_args.extend(['--output={}/{}.json'.format(self.log_dir,
            splitext(basename(job_spec))[0])])
        output = check_output([self.cmd] + self.cmd_args + cmd)

        return output

    def _parse_job(self, job_spec):
        job = self._get_parameters(job_spec)
        # which template does the job want

        template = self.jinja_env.get_template(job['template'])

        return self._populate_and_write(template, job)

    def _populate_and_write(self, template, job):
        jobfile = '{}/jobfile'.format(self.work_dir)

        # render template and save job file
        template.stream(job).dump(jobfile)
        return jobfile

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

    log_dir = ''
    if 'log_dir' in kwargs:
        log_dir = kwargs['log_dir']
        print('log dir is {}'.format(log_dir))
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

    fio = Fio(bench_dir, work_dir, log_dir)

    for job_spec in default_collection['jobs']:
        print(fio.run(job_spec))

    return True
