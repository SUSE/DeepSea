# -*- coding: utf-8 -*-

import salt.client
import salt.config

import ast
import logging
import datetime
import ipaddress
from jinja2 import Environment, FileSystemLoader
from os.path import dirname, basename, splitext
from subprocess import check_output
import sys
import yaml

log = logging.getLogger(__name__)
local_client = salt.client.LocalClient()

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

class Fio(object):

    def __init__(self, bench_dir, work_dir, log_dir, job_dir):
        '''
        get a list of the minions ip addresses and pick the one that falls into
        the public_network
        '''
        search = 'I@roles:mds-client and I@cluster:ceph'
        public_network = list(local_client.cmd(search, 'pillar.get',
                ['public_network'], expr_form='compound').values())[0]

        minion_ip_lists = local_client.cmd(search, 'network.ip_addrs', [],
                expr_form = 'compound')

        if not minion_ip_lists:
            raise Exception('No mds-client roles defined')

        clients = []
        ip_filter = lambda add: ipaddress.ip_address(add.decode()) in ipaddress.ip_network(public_network.decode())
        for minion, ip_list in minion_ip_lists.items():
            clients.extend(list(filter(ip_filter, ip_list)))

        if not clients:
            raise Exception(
            '''Mds-clients do not have an ip address in the public
            network of the Ceph Cluster.''')

        self.cmd = 'fio'

        self.cmd_args = ['--output-format=json']

        self.client_args = []
        self.client_args.extend(['--client={}'.format(client) for client in clients])

        self.bench_dir = bench_dir
        self.log_dir = log_dir
        self.work_dir = work_dir
        self.job_dir = job_dir

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
        output_args = ['--output={}/{}_{}.json'.format(self.log_dir,
            splitext(basename(job_spec))[0],
            datetime.datetime.now().strftime('%y-%m-%d_%H:%M:%S'))]
        output = check_output([self.cmd] + self.cmd_args + output_args + cmd)

        return output

    def _parse_job(self, job_spec):
        job = self._get_parameters(job_spec)
        # which template does the job want

        template = self.jinja_env.get_template(job['template'])

        return self._populate_and_write(template, job)

    def _populate_and_write(self, template, job):
        jobfile = '{}/jobfile'.format(self.job_dir)

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

    job_dir = ''
    if 'job_dir' in kwargs:
        job_dir = kwargs['job_dir']
        print('job dir is {}'.format(job_dir))
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

    fio = Fio(bench_dir, work_dir, log_dir, job_dir)

    for job_spec in default_collection['jobs']:
        print(fio.run(job_spec))

    return True

def baseline(margin = 10, verbose = False, **kwargs):
    '''
    trigger 'ceph tell osd.$n bench' on all $n OSDs and check the results for
    slow outliers
    '''
    # get all osd ids
    osd_list = local_client.cmd('I@cluster:ceph and I@roles:storage', 'osd.list', [],
                expr_form = 'compound')
    ids = [osd_id for (osd, osd_ids) in osd_list.items() for osd_id in osd_ids]

    # gotta get the master_minion...not pretty but works
    master_minion = local_client.cmd('I@roles:master', 'pillar.get',
            ['master_minion'], expr_form= 'compound').items()[0][1]

    sys.stdout.write('\nRunning osd benchmarks')
    sys.stdout.flush()
    results = []
    for id in ids:
        sys.stdout.write('.')
        sys.stdout.flush()
        output = local_client.cmd(master_minion, 'cmd.shell',
                ['ceph tell osd.{} bench'.format(id)])
        results.append(output)

    # minion output is a string, so must be parsed; ditch the key
    parsed_results = [ast.literal_eval(r[master_minion]) for r in results]

    perf_abs = [r['bytes_per_sec'] for r in parsed_results]

    avg = reduce(lambda r1, r2: r1 + r2, perf_abs)/len(perf_abs)

    print('\n\nAverage OSD performance: {}/s\n'.format(__human_size(avg)))

    dev_abs = [p - avg for p in perf_abs]
    dev_percent = [d / (avg*0.01) for d in dev_abs]

    if(verbose):
        __print_verbose(dev_percent, perf_abs, ids, margin)
    else:
        __print_outliers(dev_percent, perf_abs, ids, margin)

    return True

def __print_verbose(dev_percent, perf_abs, ids, margin):
    for d, pa, id in sorted(zip(dev_percent, perf_abs, ids), reverse=True,
            key = lambda t: t[1]):
        if(d <= -margin):
            __print_osd_deviation(id, d, pa, bcolors.FAIL)
        else:
            __print_osd_deviation(id, d, pa)
    print('\n')

def __print_outliers(dev_percent, perf_abs, ids, margin):
    outlier = False
    for d, pa, id in zip(dev_percent, perf_abs, ids):
        if(d <= -margin):
            __print_osd_deviation(id, d, pa, bcolors.FAIL)
            outlier = True
        elif(d >= margin):
            __print_osd_deviation(id, d, pa)
            outlier = True

    if not outlier:
        print('{}All osds operate within a {}% margin{}'.format(bcolors.OKGREEN,
            margin, bcolors.ENDC))
    print('\n')

def __print_osd_deviation(id, dev, perf_abs, color=bcolors.OKGREEN):
    print('{}osd.{} deviates {}{:2.2f}%{}{} from the average ({}/s){}'.format(color,
        id, bcolors.BOLD, dev, bcolors.ENDC, color, __human_size(perf_abs),
        bcolors.ENDC))

def __human_size(num, suffix='B'):
    for unit in ['','Ki','Mi','Gi','Ti','Pi','Ei','Zi']:
        if abs(num) < 1024.0:
            return "%3.1f%s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f%s%s" % (num, 'Yi', suffix)
