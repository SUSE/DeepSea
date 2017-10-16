# -*- coding: utf-8 -*-

import salt.client
import salt.config

import ast
import logging
import datetime
import ipaddress
import jinja2
import os
import subprocess
import sys
import time
import yaml

from itertools import product

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
        hostnames = []
        ip_filter = lambda add: ipaddress.ip_address(
            add.decode()) in ipaddress.ip_network(public_network.decode())
        for minion, ip_list in minion_ip_lists.items():
            clients.extend(list(filter(ip_filter, ip_list)))
            hostnames.append(minion)

        if not clients:
            raise Exception(
                '''Clients do not have an ip address in the public
                network of the Ceph Cluster.''')

        self.target = target

        self.cmd = 'fio'

        self.cmd_global_args = ['--output-format=json']

        # store client hostnames
        self.clients = hostnames

        self.bench_dir = bench_dir
        self.log_dir = log_dir
        self.work_dir = work_dir
        self.job_dir = job_dir

        self.jinja_env = jinja2.Environment(
            loader=jinja2.FileSystemLoader('{}/{}'.format(bench_dir,
                                                          'templates')))

    def run(self, job_spec):
        job_name = os.path.splitext(os.path.basename(job_spec))[0]
        log_dir = '{}/{}/{}/{}_{}'.format(
            self.log_dir,
            self.target,
            'fio',
            job_name,
            datetime.datetime.now().strftime('%y-%m-%d_%H-%M-%S'))
        os.makedirs(log_dir)

        # parse yaml and get all job permutations
        permutations_specs = self._parse_permutations_specs(job_spec, log_dir)
        job_permutations = self._get_job_permutations(permutations_specs)
        master_minion = local_client.cmd(
                        'I@roles:master', 'pillar.get',
                        ['master_minion'], expr_form='compound').items()[0][1]

        output = []
        for job in job_permutations:
            client_jobs = []
            '''
            create a list that alternates between --client arguments and job files
            e.g. [--client=host1, jobfile, --client=host2, jobfile]
            fio expects a job file for every remote agent
            '''
            job_name = '{}_{}_{}'.format(job['number_of_workers'], job['workload'], job['blocksize'])
            job_log_dir = '{}/{}'.format(log_dir, job_name)
            os.makedirs(job_log_dir)
            for client in self.clients:
                job.update({'client': client})
                jobfile = self._parse_job(job, job_name, job_log_dir, client)
                client_jobs.extend(['--client={}'.format(client)])
                client_jobs.extend([jobfile])

            log_args = ['--output={}/{}.json'.format(job_log_dir, job_name)]

            # Run fio command
            log.info('fio command:')
            log.info([self.cmd] + self.cmd_global_args + log_args + client_jobs)
            output.append(subprocess.check_output(
                [self.cmd] + self.cmd_global_args + log_args + client_jobs))

            # Some time to settle between runs
            time.sleep(30)

        return output

    def _parse_job(self, job, job_name, job_log_dir, client):
        # which template does the job want
        template = self.jinja_env.get_template(job['template'])

        # popluate template and return job file location
        return self._populate_and_write_job_file(template, job, job_name, client, job_log_dir)

    def _populate_and_write_job_file(self, template, job, job_name, client, job_log_dir):
        jobfile = '{}/{}.fio'.format(job_log_dir, client)

        # Add configs from pillars
        pool_name = local_client.cmd(
            'I@roles:master', 'pillar.get',
            ['rbd_benchmark_pool'], expr_form='compound').items()[0][1]
        job.update({'pool_name': pool_name})
        log.info('RBD benchmarks: using pool {}'.format(pool_name))

        image_prefix = local_client.cmd(
            'I@roles:master', 'pillar.get',
            ['rbd_benchmark_image_prefix'], expr_form='compound').items()[0][1]
        job.update({'image_prefix': image_prefix})
        log.info('RBD benchmarks: using image prefix {}'.format(image_prefix))

        job.update({'job_log_dir': job_log_dir})
        log.info('RBD benchmarks: using image job log dir {}'.format(job_log_dir))

        # render template and save job file
        template.stream(job).dump(jobfile)
        return jobfile

    def _parse_permutations_specs(self, permutations_specs_file, job_log_dir):
        """
        Expects a YAML file that contains all permutations.
        Returns a data structure with all permutations requested by the YAML file.

        Options on which we can permutate: number_of_workers, workload, blocksize
        """
        with open('{}/{}'.format(self.bench_dir, permutations_specs_file, 'r')) as yml:
            try:
                permutations = yaml.load(yml)
            except YAMLError as error:
                log.error('Error parsing job spec in file {}/fio/{}'.format(self.bench_dir, permutations_specs_file))
                log.error(error)
                raise error
        permutations.update({'dir': self.work_dir})
        return permutations

    def _get_job_permutations(self, permutations_spec):
        """
        Expects a data structure that describes all permutations.
        Returns an array of jobs.
        """
        list_entries = {k: v for k, v in permutations_spec.items() if isinstance(v, list)}
        keys = list_entries.keys()
        scalar_entries = {k: v for k, v in permutations_spec.items() if not isinstance(v, list)}

        permutations = list(product(*list_entries.values()))
        res = []
        for permutation in permutations:
            run = {}
            run.update(scalar_entries)
            for i in range(0, len(list_entries)):
                run.update({keys[i]: permutation[i]})
            res.append(run)
        return res


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
        'I@roles:client-rbd-benchmark and I@cluster:ceph')
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


def baseline(margin=10, verbose=False, **kwargs):
    '''
    trigger 'ceph tell osd.$n bench' on all $n OSDs and check the results for
    slow outliers
    '''
    # get all osd ids
    osd_list = local_client.cmd('I@cluster:ceph and I@roles:storage',
                                'osd.list', [], expr_form='compound')
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
