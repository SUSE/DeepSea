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
    def __init__(self, name):
        self.name = name

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

    def _collect_bucket_list(self):
        return self._exec_rgw_admin(['bucket', 'list'])

    def _collect_usage_data(self):
        return self._exec_rgw_admin(['usage', 'show', '--show-log-sum=false'])

    def _init_metrics(self):
        self._metrics = {
            'user_count': prometheus_client.core.CounterMetricFamily(
                'ceph_rgw_user_count',
                'Number of users'),
            'bucket_count': prometheus_client.core.CounterMetricFamily(
                'ceph_rgw_bucket_count',
                'Number of buckets'),
            'ops': prometheus_client.core.CounterMetricFamily(
                'ceph_rgw_user_usage_ops_total',
                'Number of operations',
                labels=["bucket", "owner", "category"]),
            'successful_ops': prometheus_client.core.CounterMetricFamily(
                'ceph_rgw_user_usage_successful_ops_total',
                'Number of successful operations',
                labels=["bucket", "owner", "category"]),
            'bytes_sent': prometheus_client.core.CounterMetricFamily(
                'ceph_rgw_user_usage_sent_bytes_total',
                'Number of bytes sent by the RADOS Gateway',
                labels=["bucket", "owner", "category"]),
            'bytes_received': prometheus_client.core.CounterMetricFamily(
                'ceph_rgw_user_usage_received_bytes_total',
                'Number of bytes received by the RADOS Gateway',
                labels=["bucket", "owner", "category"])
        }

    def _add_user_metrics(self, count):
        self._metrics['user_count'].add_metric([], count)

    def _add_bucket_metrics(self, count):
        self._metrics['bucket_count'].add_metric([], count)

    def _add_usage_metrics(self, bucket_name, bucket_owner, category):
        self._metrics['ops'].add_metric([
            bucket_name, bucket_owner,
            category['category']], category['ops'])
        self._metrics['successful_ops'].add_metric([
            bucket_name, bucket_owner,
            category['category']], category['successful_ops'])
        self._metrics['bytes_sent'].add_metric([
            bucket_name, bucket_owner,
            category['category']], category['bytes_sent'])
        self._metrics['bytes_received'].add_metric([
            bucket_name, bucket_owner,
            category['category']], category['bytes_received'])

    def collect(self):
        self._init_metrics()
        # Process number of users.
        data = self._collect_user_list()
        self._add_user_metrics(len(data))
        # Process number of buckets.
        data = self._collect_bucket_list()
        self._add_bucket_metrics(len(data))
        # Process the usage statistics.
        data = self._collect_usage_data()
        if 'entries' in data:
            for entry in data['entries']:
                for bucket in entry['buckets']:
                    for category in bucket['categories']:
                        self._add_usage_metrics(
                            bucket['bucket'],
                            bucket['owner'],
                            category)
        for metric in self._metrics.values():
            yield metric

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-n', '--name',
        metavar='TYPE.ID',
        required=False,
        type=str)
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
            registry.register(CephRgwCollector(args.name))
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
