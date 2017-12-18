# -*- coding: utf-8 -*-
# pylint: skip-file

import salt.client
import salt.config

import ast
import logging
import datetime
import ipaddress
from itertools import product
import jinja2
import os
import subprocess
import sys
import time
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

    def __init__(self, client_glob, target, bench_dir, work_dir,
                 log_dir, job_dir):
        '''
        get a list of the minions ip addresses and pick the one that falls into
        the public_network
        '''
        public_network = list(local_client.cmd(
            'I@roles:mon', 'pillar.get',
            ['public_network'], expr_form='compound').values())[0]

        minion_ip_lists = local_client.cmd(
            client_glob, 'network.ip_addrs', [], expr_form='compound')

        if not minion_ip_lists:
            raise Exception('No minions found for glob {}'.format(client_glob))

        clients = []
        ip_filter = lambda add: ipaddress.ip_address(
            add.decode()) in ipaddress.ip_network(public_network.decode())
        for minion, ip_list in minion_ip_lists.items():
            clients.extend(list(filter(ip_filter, ip_list)))

        if not clients:
            raise Exception(
                '''Clients do not have an ip address in the public
                network of the Ceph Cluster.''')

        self.target = target

        self.cmd = 'fio'

        self.cmd_global_args = ['--output-format=json']

        # store client addresses preformatted for user with fio
        self.clients = clients
        self.client_glob = client_glob
        self.bench_dir = bench_dir
        self.log_dir = log_dir
        self.work_dir = work_dir
        self.job_dir = job_dir

        self.jinja_env = jinja2.Environment(
            loader=jinja2.FileSystemLoader('{}/{}'.format(bench_dir,
                                                          'templates')))

    def run(self, job_spec):
        job_name = os.path.splitext(os.path.basename(job_spec))[0]
        job_log_dir = '{}/{}/{}/{}_{}'.format(
            self.log_dir,
            self.target,
            'fio',
            job_name,
            datetime.datetime.now().strftime('%y-%m-%d_%H-%M-%S'))
        os.makedirs(job_log_dir)

        runner = salt.runner.RunnerClient(salt.config.client_config('/etc/salt/master'))

        job = self._get_job_parameters(job_spec, job_log_dir)
        # parse yaml and get job spec
        job_product = self._get_exploded_job(job)

        output = []
        for job in job_product:
            client_jobs = []
            '''
            create a list that alternates between --client arguments and job files
            e.g. [--client=host1, jobfile, --client=host2, jobfile]
            fio expects a job file for every remote agent
            '''
            job_name = '{}_{}_{}'.format(job['number_of_workers'], job['op'], job['bs'])
            for client in self.clients:
                job.update({'client': client})
                jobfile = self._parse_job(job, job_name, job_log_dir, client)
                client_jobs.extend(['--client={}'.format(client)])
                client_jobs.extend([jobfile])

            log_args = ['--output={}/{}.json'.format(job_log_dir, job_name)]
            print('Running job {}'.format(job_name))
            output.append(subprocess.check_output(
                [self.cmd] + self.cmd_global_args + log_args + client_jobs))
            minion = runner.cmd('select.one_minion', ['cluster=ceph',
                                'roles=client--{}'.format(self.client_glob)],
                               print_event=False)
            print('Job done...using {} to cleanup bench files'.format(minion))
            local_client.cmd(minion, 'cmd.run', ['rm {}/*'.format(self.work_dir)])
            time.sleep(60)

        return output

    def _get_exploded_job(self, job):
        list_entries = {k: v for k, v in job.items() if isinstance(v, list)}
        list_keys = list_entries.keys()
        scalar_values = {k: v for k, v in job.items() if not isinstance(v, list)}
        perms = list(product(*list_entries.values()))
        res = []
        for perm in perms:
            job = {}
            job.update(scalar_values)
            for i in range(0, len(list_entries)):
                job.update({list_keys[i]: perm[i]})
            res.append(job)
        return res

    def _parse_job(self, job, job_name, job_log_dir, client):
        # which template does the job want
        template = self.jinja_env.get_template(job['template'])

        # popluate template and return job file location
        return self._populate_and_write_job(template, job, job_name, client, job_log_dir)

    def _populate_and_write_job(self, template, job, job_name, client, job_log_dir):
        jobfile = '{}/{}_{}'.format(job_log_dir, job_name, client)

        # render template and save job file
        template.stream(job).dump(jobfile)
        return jobfile

    def _get_job_parameters(self, job_spec, job_log_dir):
        with open('{}/{}'.format(self.bench_dir, job_spec, 'r')) as yml:
            try:
                job = yaml.load(yml)
            except YAMLError as error:
                log.error('Error parsing job spec in file {}/fio/{}'.format(self.bench_dir, job_spec))
                log.error(error)
                raise error
        output_options = '''
        #write_bw_log={logdir}/output
        #write_lat_log={logdir}/output
        #write_hist_log={logdir}/output
        #write_iops_log={logdir}/output
        '''.format(logdir=job_log_dir)
        job.update({'dir': self.work_dir,
                    'output_options': output_options,
                   })
        return job


def __parse_and_set_dirs(kwargs):
    '''
    check kwargs for passed directory locations and return a dict with the
    directory locations set presence of directories is not checked...they are
    just expected to be there.  work_dir is only present on cephfs instance and
    can not be check from the salt-master by default. Dirs are created by salt
    state file.
    '''
    dir_options = {}
    work_dir = ''
    for option in ['work_dir', 'log_dir', 'job_dir']:
        if option in kwargs:
            dir_options[option] = kwargs[option]
            log.info('{} is {}'.format(option, work_dir))
        else:
            raise KeyError('{} not specified'.format(option))
            return 1

    __opts__ = salt.config.client_config('/etc/salt/master')
    # bench_dir = ''
    for ext in __opts__['ext_pillar']:
        if 'stack' in ext:
            # TODO only add benchmark.cfg here. Salt returns either a string
            # (when there is on ext_module) or an array :(
            # This needs a better solution...works only if benchmark.cfg is 2nd
            # entry in ext_modules
            dir_options['bench_dir'] = os.path.dirname(ext['stack'][1])

    return dir_options


def __parse_collection(collection_file):
    with open(collection_file, 'r') as yml:
        try:
            return yaml.load(yml)
        except YAMLError as error:
            log.error('Error parsing collection {}:'.format(collection_file))
            log.error(error)
            raise error


def help():
    """
    Usage
    """
    usage = ('salt-run benchmark.rbd work_dir=/path log_dir=/path job_dir=/path default_collection=simple.yml client_glob=target:\n\n'
             '    Run RBD benchmarks\n'
             '\n\n'
             'salt-run benchmark.cephfs work_dir=/path log_dir=/path job_dir=/path default_collection=simple.yml client_glob=target:\n\n'
             '    Run CephFS benchmarks\n'
             '\n\n'
             'salt-run benchmark.baseline work_dir=/path log_dir=/path job_dir=/path default_collection=simple.yml client_glob=target:\n\n'
             '    Run Baseline benchmarks\n'
             '\n\n'
    )
    print usage
    return ""

def rbd(**kwargs):
    """
    Run rbd benchmark job
    """

    client_glob = kwargs.get('client_glob',
        'I@roles:benchmark-rbd and I@cluster:ceph')
    log.info('client glob is {}'.format(client_glob))

    dir_options = __parse_and_set_dirs(kwargs)

    default_collection = __parse_collection(
        '{}/collections/default.yml'.format(dir_options['bench_dir']))

    fio = Fio(client_glob, 'rbd',
              dir_options['bench_dir'],
              dir_options['work_dir'],
              dir_options['log_dir'],
              dir_options['job_dir'])

    for job_spec in default_collection['rbd']:
        print(fio.run(job_spec))

    return True


def cephfs(**kwargs):
    """
    Run cephfs benchmark jobs
    """

    client_glob = kwargs.get('client_glob',
                             'I@roles:client-cephfs and I@cluster:ceph')
    log.info('client glob is {}'.format(client_glob))

    dir_options = __parse_and_set_dirs(kwargs)

    default_collection = __parse_collection(
        '{}/collections/default.yml'.format(dir_options['bench_dir']))

    fio = Fio(client_glob, 'cephfs',
              dir_options['bench_dir'],
              dir_options['work_dir'],
              dir_options['log_dir'],
              dir_options['job_dir'])

    for job_spec in default_collection['fs']:
        print(fio.run(job_spec))

    return True

def ganesha(**kwargs):
    """
    Run ganesha benchmark jobs
    """

    client_glob = kwargs.get('client_glob','I@roles:client-nfs')
    log.info('client glob is {}'.format(client_glob))

    dir_options = __parse_and_set_dirs(kwargs)

    default_collection = __parse_collection(
        '{}/collections/default.yml'.format(dir_options['bench_dir']))

    fio = Fio(client_glob, 'ganesha',
              dir_options['bench_dir'],
              dir_options['work_dir'],
              dir_options['log_dir'],
              dir_options['job_dir'])

    for job_spec in default_collection['fs']:
        print(fio.run(job_spec))

    return True

def baseline(margin=10, verbose=False, **kwargs):
    '''
    trigger 'ceph tell osd.$n bench' on all $n OSDs and check the results for
    slow outliers
    '''
    client_glob = kwargs.get('client_glob',
                             'I@roles:storage and I@cluster:ceph')
    log.info('client glob is {}'.format(client_glob))

    # get all osd ids for a given client_glob
    osd_list = local_client.cmd(client_glob,
        'osd.list', [], expr_form='compound')

    if not osd_list:
        raise Exception('No OSDs found for glob {}'.format(client_glob))

    ids = [osd_id for (osd, osd_ids) in osd_list.items() for osd_id in osd_ids]

    # gotta get the master_minion...not pretty but works
    master_minion = local_client.cmd(
        'I@roles:master', 'pillar.get',
        ['master_minion'], expr_form='compound').items()[0][1]

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
        print('{}All osds operate within a {}% margin{}'.format(
            bcolors.OKGREEN,
            margin, bcolors.ENDC))
    print('\n')


def __print_osd_deviation(id, dev, perf_abs, color=bcolors.OKGREEN):
    print('{}osd.{} deviates {}{:2.2f}%{}{} from the average ({}/s){}'.format(
        color,
        id, bcolors.BOLD, dev, bcolors.ENDC, color, __human_size(perf_abs),
        bcolors.ENDC))


def __human_size(num, suffix='B'):
    for unit in ['', 'Ki', 'Mi', 'Gi', 'Ti', 'Pi', 'Ei', 'Zi']:
        if abs(num) < 1024.0:
            return "%3.1f%s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f%s%s" % (num, 'Yi', suffix)
