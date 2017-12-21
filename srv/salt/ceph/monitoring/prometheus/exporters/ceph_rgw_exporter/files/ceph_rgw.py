#!/usr/bin/python
# -*- coding: utf-8 -*-

import argparse
import fcntl
import json
import os
import prometheus_client
import subprocess
import sys
import syslog

class CephRgwCollector(object):
    def __init__(self, name, disable_bucket_metrics, disable_user_metrics):
        self.name = name
        self.disable_bucket_metrics = disable_bucket_metrics
        self.disable_user_metrics = disable_user_metrics

    def _exec_rgw_admin(self, args):
        try:
            cmd_args = ['radosgw-admin']
            if self.name is not None:
                cmd_args.append('--name')
                cmd_args.append(self.name)
            cmd_args.extend(args)
            out = subprocess.check_output(cmd_args)
            return json.loads(out.decode())
        except Exception as e:
            syslog.syslog(syslog.LOG_ERR, str(e))
            return {}

    def _collect_user_list(self):
        return self._exec_rgw_admin(['metadata', 'list', 'user'])

    def _collect_bucket_stats(self):
        return self._exec_rgw_admin(['bucket', 'stats'])

    def _init_metrics(self):
        self._metrics = {}

    def _init_user_metrics(self):
        self._metrics.update({
            'user_count': prometheus_client.core.CounterMetricFamily(
                'ceph_rgw_user_count',
                'Number of users')
        })

    def _init_bucket_metrics(self):
        self._metrics.update({
            'bucket_count': prometheus_client.core.CounterMetricFamily(
                'ceph_rgw_bucket_count',
                'Number of buckets'),
            'bucket_stats_size_actual': prometheus_client.core.CounterMetricFamily(
                'ceph_rgw_bucket_stats_size_actual',
                'Actual bucket size',
                labels=["bucket", "owner"]),
            'bucket_stats_size_utilized': prometheus_client.core.CounterMetricFamily(
                'ceph_rgw_bucket_stats_size_utilized',
                'Utilized bucket size',
                labels=["bucket", "owner"]),
            'bucket_stats_num_objects': prometheus_client.core.CounterMetricFamily(
                'ceph_rgw_bucket_stats_num_objects',
                'Number of objects in bucket',
                labels=["bucket", "owner"])
        })

    def _add_user_metrics(self, count):
        self._metrics['user_count'].add_metric([], count)

    def _add_bucket_metrics(self, data):
        self._metrics['bucket_count'].add_metric([], len(data))
        for bucket in data:
            if not 'rgw.main' in bucket['usage'] or not bucket['usage']['rgw.main'].keys():
                bucket['usage']['rgw.main'] = {}
                bucket['usage']['rgw.main']['size_actual'] = 0
                bucket['usage']['rgw.main']['size_utilized'] = 0
                bucket['usage']['rgw.main']['num_objects'] = 0
            self._metrics['bucket_stats_size_actual'].add_metric([
                bucket['bucket'], bucket['owner']],
                bucket['usage']['rgw.main']['size_actual'])
            self._metrics['bucket_stats_size_utilized'].add_metric([
                bucket['bucket'], bucket['owner']],
                bucket['usage']['rgw.main']['size_utilized'])
            self._metrics['bucket_stats_num_objects'].add_metric([
                bucket['bucket'], bucket['owner']],
                bucket['usage']['rgw.main']['num_objects'])

    def collect(self):
        self._init_metrics()
        # Process number of users.
        if not self.disable_user_metrics:
            self._init_user_metrics()
            data = self._collect_user_list()
            self._add_user_metrics(len(data))
        # Process number of buckets.
        if not self.disable_bucket_metrics:
            self._init_bucket_metrics()
            data = self._collect_bucket_stats()
            self._add_bucket_metrics(data)
        for metric in self._metrics.values():
            yield metric

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-n', '--name',
        metavar='TYPE.ID',
        required=False,
        type=str)
    parser.add_argument(
        '--disable-user-metrics',
        action='store_true',
        required=False)
    parser.add_argument(
        '--disable-bucket-metrics',
        action='store_true',
        required=False)
    return parser.parse_args()

def main():
    exit_status = 1
    try:
        args = parse_args()
        # Make sure the exporter is only running once.
        lock_file = '/var/lock/{}.lock'.format(os.path.basename(sys.argv[0]))
        lock_fd = os.open(lock_file, os.O_CREAT)
        lock_success = False
        try:
            fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            lock_success = True
        except IOError:
            msg = 'Failed to export metrics, another instance is running.'
            syslog.syslog(syslog.LOG_INFO, msg)
            sys.stderr.write(msg + '\n')
        if lock_success:
            # Create a new registry, otherwise unwanted default collectors are
            # added automatically.
            registry = prometheus_client.CollectorRegistry()
            # Register our own collector and write metrics to STDOUT.
            registry.register(CephRgwCollector(**vars(args)))
            sys.stdout.write(prometheus_client.generate_latest(registry))
            sys.stdout.flush()
            # Unlock the lock file.
            fcntl.flock(lock_fd, fcntl.LOCK_UN)
            exit_status = 0
    except Exception as e:
        syslog.syslog(syslog.LOG_ERR, str(e))
    # Cleanup
    os.close(lock_fd)
    if lock_success:
        try:
            os.unlink(lock_file)
        except:
            pass
    sys.exit(exit_status)

if __name__ == "__main__":
    main()
