# -*- coding: utf-8 -*-
# vim: ts=8 et sw=4 sts=4

import os

def _extract_key(filename):
    # This is pretty similar to keyring.secret()...
    if os.path.exists(filename):
        with open(filename, 'r') as keyring:
            for line in keyring:
                if "key" in line and " = " in line:
                    return line.split(" = ")[1].strip()
    return ""

def inspect(**kwargs):
    # This will *ONLY* work on a cluster named "ceph".  It won't help with
    # clusters with other names.

    # deliberately only looking for things ceph-deploy can deploy
    # TODO: do we need more than this?
    ceph_services = ['ceph-mon', 'ceph-osd', 'ceph-mds', 'ceph-radosgw']

    #
    # running_services will be something like:
    #
    # {
    #   'ceph-mon': [ 'hostname' ],
    #   'ceph-osd': [ '0', '1', '2', ... ]
    # }
    #
    running_services = {}
    for rs in __salt__['service.get_running']():
        instance = rs.split('@')
        if len(instance) == 2 and instance[0] in ceph_services:
            if not running_services.has_key(instance[0]):
                running_services[instance[0]] = []
            running_services[instance[0]].append(instance[1])

    ceph_keys = {}

    ceph_keys["ceph.client.admin"] = _extract_key("/etc/ceph/ceph.client.admin.keyring")
    ceph_keys["bootstrap-osd"] = _extract_key("/var/lib/ceph/bootstrap-osd/ceph.keyring")

    if "ceph-mon" in running_services.keys():
        # Theoretically it's possible to run more than one MON per node, but
        # Nobody Will Ever Do That[TM], and in any case, all MONs share the same
        # key, so just grab the first (hopefully only) one.
        ceph_keys["mon"] = _extract_key("/var/lib/ceph/mon/ceph-" + running_services["ceph-mon"][0] + "/keyring")

    if "ceph-mds" in running_services.keys():
        ceph_keys["mds"] = {}
        for instance in running_services["ceph-mds"]:
            ceph_keys["mds"][instance] = _extract_key("/var/lib/ceph/mds/ceph-" + instance + "/keyring")

    if "ceph-radosgw" in running_services.keys():
        ceph_keys["rgw"] = {}
        for instance in running_services["ceph-radosgw"]:
            ceph_keys["rgw"][instance] = _extract_key("/var/lib/ceph/radosgw/ceph-" + instance + "/keyring")

    ceph_conf = None
    try:
        with open("/etc/ceph/ceph.conf", "r") as conf:
            ceph_conf = conf.read()
    except:
        pass

    # note that some keys will be empty strings if not present, e.g. it's
    # possible to have ceph_keys['ceph.client.admin'] == '', so don't just
    # rely on ceph.client.admin being present in the dict, check its value
    # before using it.
    return {
        "running_services": running_services,
        "ceph_keys": ceph_keys,
        "ceph_conf": ceph_conf
    }
