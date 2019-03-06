# -*- coding: utf-8 -*-
# pylint: disable=incompatible-py3-code

"""
Partitions prometheus scrape targets accoring to pillar data.
This assume a minion has received all scrape_targets. This module removes
scrape_target, that this minion is not supposed to have according to pillar
configuration.
Currently supported pillar data:
    n/m: a string with two integers divided by a '/'. Partition list of scrape
    targets into m partitions and keep partition n, delete the rest. 0/m will
    remove all scrape targets.
"""

import logging
import os

log = logging.getLogger(__name__)


def _partition_by_division(scrape_targets, partition_to_keep,
                           total_partitions):
    '''
    :param scrape_targets: a list of which only a partition is to be kept
    :param partition_to_keep: index of partition to keep
    :param: total_partitions: the number of partitions
    :returns: a set of items in scrape_targets, that does not fall in the
      partition_to_keep
    :raises IndexError: if partition_to_keep > total_partitions
    '''
    partition_length = len(scrape_targets) / total_partitions

    def index(length, i):
        '''
        Return the rounded index of the i'th partition with length items per
        partition
        '''
        return round(length * i)
    partitions = [scrape_targets[index(partition_length, i):
                                 index(partition_length, i + 1)]
                  for i in range(total_partitions)]
    return set(scrape_targets).difference(
        set(partitions[partition_to_keep - 1]))


def partition(exporter='node_exporter'):
    '''
    partition a nodes scrape targets. The partitioning specification in stored
    in the pillar. The format is 'n/m' meaning partition all scrape targets in
    to m partitions and keep partition number n on this node.
    '''

    pillar = 'monitoring:prometheus:target_partition:{}'.format(exporter)
    part_pillar = __salt__['pillar.get'](pillar)
    if part_pillar == '1/1':
        # nothing to do
        return True

    if '/' not in part_pillar:
        log.error('{} has the wrong format: {}'.format(pillar, part_pillar))
        return False

    # __salt__['state.apply']('ceph.monitoring.prometheus.push_scrape_configs')

    local_part, all_parts = part_pillar.split('/')
    scrape_target_path = '/etc/prometheus/SUSE/{}/'.format(exporter)

    targets = sorted(os.listdir(scrape_target_path))
    to_remove = []
    if local_part == 0:
        to_remove = targets
    else:
        to_remove = _partition_by_division(targets, local_part, all_parts)

    for filename in to_remove:
        file_ = '{}/{}'.format(scrape_target_path, filename)
        log.info('removing scrape target {}'.format(file_))
        os.remove(file_)

    return True
