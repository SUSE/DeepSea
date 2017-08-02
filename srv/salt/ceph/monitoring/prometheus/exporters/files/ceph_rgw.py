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
    def _request_data(self):
        try:
            out = subprocess.check_output(['radosgw-admin', 'usage', 'show',
                '--show-log-sum=false'])
            return json.loads(out.decode())
        except Exception as e:
            syslog.syslog(syslog.LOG_ERR, str(e))
            return {}

    def _init_metrics(self):
        self._metrics = {
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

    def _add_metrics(self, bucket_name, bucket_owner, category):
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
        data = self._request_data()
        self._init_metrics()
        if 'entries' in data:
            for entry in data['entries']:
                for bucket in entry['buckets']:
                    for category in bucket['categories']:
                        self._add_metrics(
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
