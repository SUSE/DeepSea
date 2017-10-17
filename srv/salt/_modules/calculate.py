# -*- coding: utf-8 -*-

import salt.client

local_client = salt.client.LocalClient()

def _nearest_power_of_two(target):
    if target <= 0:
        raise Exception('Can\'t find nearest power of two of invalid value')

    i = 0

    # Based on the logic presented on http://ceph.com/pgcalc/
    while True:
        current = 2 ** i
        next = 2 ** (i + 1)

        if abs(current - target) < abs(next - target):
            # "If the nearest power of 2 is more than 25% below the
            # original value, the next higher power of 2 is used."
            if current < (target * 0.75):
                return next
            return current
        else:
            i += 1

def pg_num():
    """
    Returns the optimal number of PGs for a new pool.
    """
    osd_list = local_client.cmd('I@cluster:ceph and I@roles:storage',
                                'osd.list', [], expr_form='compound')
    pgs_per_osd = 100
    num_osd = len(osd_list)
    if num_osd == 0:
        raise Exception('Could not calculate pg_num: no OSDs found')

    num_replicas = 3
    return _nearest_power_of_two(pgs_per_osd * num_osd / num_replicas)
