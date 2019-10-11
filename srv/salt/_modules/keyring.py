# -*- coding: utf-8 -*-
""" Calls out to ceph-daemon to generate keyrings """

from ext_lib.utils import _run_cmd


def mon(hostname):
    # Whatever the syntax will be
    cmd = f"echo ceph-daemon --image foo create mon keyring for {hostname}"

    ret = _run_cmd(
        cmd, func_name=mon.__name__, module_name='keyring', hostname=hostname)
    return ret.__dict__


def mon_failure(hostname):
    # Whatever the syntax will be
    cmd = f"ceph-daemon --image foo create mon keyring for {hostname}"

    ret = _run_cmd(
        cmd,
        func_name=mon_failure.__name__,
        # get the module_name dynamically
        module_name='keyring',
        hostname=hostname)
    return ret.__dict__
