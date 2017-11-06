# -*- coding: utf-8 -*-
"""
Cleanup related operations for resetting the Salt environment and removing
a Ceph cluster
"""

from __future__ import absolute_import
import logging
import os
import shutil
import pwd
import grp
import yaml

log = logging.getLogger(__name__)


def configuration():
    """
    Purge all the necessary DeepSea related configurations

    Note: leave proposals out for now, some may want to minimally roll back
    without rerunning Stage 1
    """
    roles()
    default()


def roles():
    """
    Remove the roles from the cluster/*.sls files
    """
    # Keep yaml human readable/editable
    friendly_dumper = yaml.SafeDumper
    friendly_dumper.ignore_aliases = lambda self, data: True

    cluster_dir = '/srv/pillar/ceph/cluster'
    for filename in os.listdir(cluster_dir):
        pathname = "{}/{}".format(cluster_dir, filename)
        content = None
        with open(pathname, "r") as sls_file:
            content = yaml.safe_load(sls_file)
        log.info("content {}".format(content))
        if 'roles' in content:
            content.pop('roles')
        with open(pathname, "w") as sls_file:
            sls_file.write(yaml.dump(content, Dumper=friendly_dumper,
                           default_flow_style=False))


def proposals():
    """
    Remove all the generated subdirectories in .../proposals
    """
    proposals_dir = '/srv/pillar/ceph/proposals'
    for path in os.listdir(proposals_dir):
        for partial in ['role-', 'cluster-', 'profile-', 'config']:
            if partial in path:
                log.info("removing {}/{}".format(proposals_dir, path))
                shutil.rmtree("{}/{}".format(proposals_dir, path))


def default():
    """
    Remove the .../stack/defaults directory.  Preserve available_roles
    """
    # Keep yaml human readable/editable
    friendly_dumper = yaml.SafeDumper
    friendly_dumper.ignore_aliases = lambda self, data: True

    preserve = {}
    content = None
    pathname = "/srv/pillar/ceph/stack/default/{}/cluster.yml".format('ceph')
    with open(pathname, "r") as sls_file:
        content = yaml.safe_load(sls_file)
    preserve['available_roles'] = content['available_roles']
    stack_default = "/srv/pillar/ceph/stack/default"
    shutil.rmtree(stack_default)
    os.makedirs("{}/{}".format(stack_default, 'ceph'))
    with open(pathname, "w") as sls_file:
        sls_file.write(yaml.dump(preserve, Dumper=friendly_dumper,
                       default_flow_style=False))

    uid = pwd.getpwnam("salt").pw_uid
    gid = grp.getgrnam("salt").gr_gid
    for path in [stack_default, "{}/{}".format(stack_default, 'ceph'), pathname]:
        os.chown(path, uid, gid)
