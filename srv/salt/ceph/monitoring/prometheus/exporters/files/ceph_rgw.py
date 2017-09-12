#!/usr/bin/python
# -*- coding: utf-8 -*-

import argparse
import json
import prometheus_client
import socket
import subprocess
import sys
import syslog
import time

class CephRgwCollector(object):
    def _exec_rgw_admin(self, args):
        try:
            out = subprocess.check_output(['radosgw-admin'] + args)
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
        '-p', '--port',
        metavar='port',
        required=False,
        type=int,
        help='Listen locally to this port',
        default=9156)
    return parser.parse_args()

def main():
    try:
        args = parse_args()
        # Register collector and start HTTP server.
        prometheus_client.REGISTRY.register(CephRgwCollector())
        prometheus_client.start_http_server(args.port)
        # Print message to STDOUT and syslog.
        message = 'Listening on http://{}:{}\n'.format(socket.getfqdn(),
            args.port)
        sys.stdout.write(message)
        syslog.syslog(syslog.LOG_INFO, message)
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        exit(0)
    except Exception as e:
        syslog.syslog(syslog.LOG_ERR, str(e))
        exit(1)

if __name__ == "__main__":
    main()
