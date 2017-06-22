# -*- coding: utf-8 -*-
# vim: ts=8 et sw=4 sts=4

import os
import socket
from subprocess import Popen, PIPE
import json
import psutil

def _get_listening_ipaddr(proc_name):
    """
    Search for the first instance of proc_name and return the first instance of a
    listening IP address.  If proc_name or a listening IP are not found, return None.
    """
    proc_listening_ip = None

    for proc in psutil.process_iter():
	# Note that depending on psutil version, there are slight api differences, hence the
	# try/except blocks below.
	try:
	    name = proc.name()
	except:
	    name = proc.name
	if name == proc_name:
	    try:
		conns = proc.get_connections(kind="inet")
	    except:
		conns = proc.connections(kind="inet")
	    for con in conns:
		if con.status == "LISTEN":
		    proc_listening_ip = con.laddr[0]

    return proc_listening_ip

def get_minion_public_network():
    """
    Returns the listening IP of the ceph-mon process encountered first on the system.
    If ceph-mon is not running/listening, returns None.
    """
    return _get_listening_ipaddr("ceph-mon")

def get_minion_cluster_network():
    """
    Returns the listening IP of the ceph-osd process encountered first on the system.
    If ceph-osd is not running/listening, returns None.
    """
    return _get_listening_ipaddr("ceph-osd")

def _get_disk_id(partition):
    """
    Return the disk id of a partition/device, or an empty string if not available.
    """
    disk_id_cmd = Popen("find -L /dev/disk/by-id -samefile " + partition + " \( -name ata* -o -name nvme* \)", stdout=PIPE, stderr=PIPE, shell=True)
    out, err = disk_id_cmd.communicate()

    # We should only ever have one entry that we return.
    return out.rstrip()

def _append_to_ceph_disk(ceph_disks, partition, journal_dev):
    """
    Populate ceph_disks dictionary with data and journal partitions.
    """

    # We don't care about the trailing number on journal_dev.
    journal_dev = journal_dev.rstrip("1234567890")
    # For nvme journal, strip the trailing 'p' as well.
    if "nvme" in journal_dev:
        journal_dev = journal_dev[:-1]

    # Try to obtain disk id's for data partition (device) and journal partition.
    partition_id = _get_disk_id(partition)
    journal_dev_id = _get_disk_id(journal_dev)

    partition = partition_id if partition_id else partition
    journal_dev = journal_dev_id if journal_dev_id else journal_dev

    try:
	ceph_disks["ceph"]["storage"]["osds"][partition]
    except KeyError, e:
	ceph_disks["ceph"]["storage"]["osds"][partition] = {}
    finally:
	ceph_disks["ceph"]["storage"]["osds"][partition]["format"] = "filestore"
	ceph_disks["ceph"]["storage"]["osds"][partition]["journal"] = journal_dev

def get_ceph_disks_yml(**kwargs):
    """
    Generates yml representation of Ceph filestores on a given node.
    Returns something like: {"ceph": {"storage": {"osds": {"/dev/foo":
							    {"format": "filestore",
							     "journal": "/dev/bar"}}}}}
    """
    ceph_disk_list = Popen("ceph-disk list --format=json", stdout=PIPE, stderr=PIPE, shell=True)
    out, err = ceph_disk_list.communicate()
    ceph_disks = {"ceph":
		  {"storage":
		   {"osds": {} }}}

    # Failed `ceph-disk list`
    if err: return None

    out_list = json.loads(out)
    # [ { 'path': '/dev/foo', 'partitions': [ {...}, ... ], ... }, ... ]
    # The partitions list has all the goodies.
    for part_dict in out_list:
        if not part_dict.has_key("partitions"):
            # This can happen if we encounter a CD/DVD (/dev/sr0)
            continue
	path = part_dict['path']
	for p in part_dict['partitions']:
	    if p['type'] == 'data':
		_append_to_ceph_disk(ceph_disks, path, p['journal_dev'])

    return ceph_disks

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

    ceph_conf = None
    try:
        with open("/etc/ceph/ceph.conf", "r") as conf:
            ceph_conf = conf.read()
    except:
        pass

    return {
        "running_services": running_services,
        "ceph_conf": ceph_conf,
        "has_admin_keyring": "/etc/ceph/ceph.client.admin.keyring"
    }

def get_keyring(**kwargs):
    """
    Retrieve a keyring via `ceph auth get`.  Pass key=NAME_OF_KEY,
    e.g.: use key=client.admin to get the client admin key.

    Returns either the complete keyring (suitable for use in a ceph keyring
    file), or None if the key does not exist, or cannot be obtained.

    This needs to be run on a minion with a suitable ceph.conf and client
    admin keyring, in order for `ceph auth get` to be able to talk to the
    cluster.
    """
    if not "key" in kwargs:
        return None

    cmd = Popen("ceph auth get " + kwargs["key"], stdout=PIPE, stderr=PIPE, shell=True)
    out, err = cmd.communicate()

    return out if out else None
