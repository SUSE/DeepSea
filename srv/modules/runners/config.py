# -*- coding: utf-8 -*-
'''
Salt runner for reading the policy.cfg, creating the role assignments and
global configuration files.
'''
from __future__ import absolute_import
import errno
import os
import logging
import pprint
import uuid
import sys
import yaml

import salt.key
import salt.client
import salt.runner
from ext_lib.utils import master_minion, evaluate_state_return
from ext_lib.network import DeepSeaNetwork

log = logging.getLogger(__name__)

MINIONS_DIR = "/srv/pillar/ceph/minions"
POLICY = "/srv/pillar/ceph/proposals/policy.cfg"
GLOBAL_YML = "/srv/pillar/ceph/global.yml"
CUSTOM_YML = "/srv/pillar/ceph/custom.yml"


class DeepSeaRoles(object):
    ''' Drives creation of /srv/pillar/ceph/minions '''

    def __init__(self, roles, minions_dir=MINIONS_DIR):
        self.dir = minions_dir
        self.roles = roles
        self.error = ""
        self.minions = {}
        self.dumper = yaml.SafeDumper
        self.dumper.ignore_aliases = lambda self, data: True

    def invert(self):
        ''' Swaps keys and values '''
        for key, value in self.roles.items():
            for item in value:
                self.minions.setdefault(item, []).append(key)
        log.info(f"Minions:\n{pprint.pformat(self.minions)}")

    def write(self):
        ''' Save each minion configuration '''
        if self._mkdir(self.dir):
            for minion in self.minions:
                filename = f"{self.dir}/{minion}.sls"

                stripped = [role.lstrip('role-') for role in self.minions[minion]]
                contents = {'roles': stripped}
                log.info(f"Writing {filename}")
                log.info(f"Contents {contents}")
                try:
                    with open(filename, "w") as yml:
                        yml.write(yaml.dump(contents, Dumper=self.dumper,
                                  default_flow_style=False))
                except IOError as error:
                    self.error = f"Could not write {filename}: {error}"
                    return False
            return True
        return False

    def _mkdir(self, path):
        ''' Create directory if necessary '''
        if os.path.isdir(path):
            return True

        try:
            os.makedirs(path)
            return True
        except OSError as error:
            if error.errno == errno.EACCES:
                self.error = (
                    f"Cannot create directory {path} - verify that {self.root} "
                    f"is owned by salt"
                )
        return False


# pylint: disable=too-few-public-methods
class DeepSeaCustom(object):
    ''' Drives creation of /srv/pillar/ceph/minions '''

    def __init__(self, contents, custom=CUSTOM_YML):
        ''' '''
        self.custom = custom
        self.error = ""
        self.contents = contents
        self.dumper = yaml.SafeDumper
        self.dumper.ignore_aliases = lambda self, data: True

    def write(self):
        ''' Save each minion configuration '''
        filename = f"{self.custom}"

        log.info(f"Writing {filename}")
        log.info(f"Contents {self.contents}")
        try:
            with open(filename, "w") as yml:
                yml.write(yaml.dump(self.contents, Dumper=self.dumper,
                          default_flow_style=False))
        except IOError as error:
            self.error = f"Could not write {filename}: {error}"
            return False
        return True


class Policy(object):
    '''
    Loads and expands the policy.cfg
    '''

    def __init__(self, policy=POLICY):
        '''  '''
        self.filename = policy
        self.error = ""
        self.raw = {}
        self.yaml = {}
        self.custom = {}

    def load(self):
        ''' Read policy.cfg '''
        if not os.path.isfile(self.filename):
            self.error = f"filename {self.filename} is missing"
            return False

        with open(self.filename, 'r') as policy:
            try:
                self.raw = yaml.load(policy)
                log.info(f"Contents of {self.filename}: \n{pprint.pformat(self.raw)}")
                return True
            except yaml.YAMLError as error:
                self.error = (
                    f"syntax error in {error.problem_mark.name} "
                    f"on line {error.problem_mark.line} in position "
                    f"{error.problem_mark.column}"
                )
            return False

    def expand(self):
        ''' Expand each Salt target '''
        for role in self.raw:
            if role.startswith("role-"):
                self.yaml[role] = self._expand(self.raw[role])
            else:
                # custom entry
                for custom_role in self.raw[role]:
                    self.yaml[custom_role] = self._expand(self.raw[role][custom_role])
                self.custom[f"{role}_configurations"] = list(self.raw[role].keys())

        log.info(f"Expanded contents:\n{pprint.pformat(self.yaml)}")
        if self.custom:
            log.info(f"Custom contents:\n{pprint.pformat(self.custom)}")

    def _expand(self, target):
        ''' Resolve Salt target '''
        local = salt.client.LocalClient()
        # When search matches no minions, salt prints to stdout.  Suppress stdout.
        _stdout = sys.stdout
        sys.stdout = open(os.devnull, 'w')

        try:
            results = local.cmd(target, 'test.true', [], tgt_type="compound")
            sys.stdout = _stdout
        except SaltClientError as error:
            sys.stdout = _stdout
            log.error(f"salt '{target}' test.true failed... {error}")
        return sorted(results)


class DeepSeaGlobal(object):
    ''' Writes the initial /srv/pillar/ceph/global.yml '''

    def __init__(self, global_yml=GLOBAL_YML):
        ''' Initial global values '''
        self.filename = global_yml
        self.error = ""
        self.contents = {}
        self.contents['fsid'] = str(uuid.uuid4())
        self.contents['time_server'] = f"{master_minion()}"
        self.contents['mgmt_network'] = ""
        self.contents['public_network'] = ""
        self.contents['cluster_network'] = ""
        self.dumper = yaml.SafeDumper
        self.dumper.ignore_aliases = lambda self, data: True

    def absent(self):
        ''' Check for global file '''
        if os.path.exists(self.filename):
            print(f"File {self.filename} already exists - not overwriting")
            return False
        return True

    def networks(self, mgmt, public, cluster):
        ''' Assign networks '''
        self.contents['mgmt_network'] = mgmt
        self.contents['public_network'] = public
        self.contents['cluster_network'] = cluster

    def write(self):
        ''' Create yaml file '''
        if self.absent():
            try:
                with open(self.filename, "w") as yml:
                    yml.write(yaml.dump(self.contents, Dumper=self.dumper,
                              default_flow_style=False))
            except IOError as error:
                self.error = f"Could not write {self.filename}: {error}"
                return False
            return True
        self.error = f"File {self.filename} exists"
        return False


def deploy(*args):
    ''' Creates Salt configuration '''

    if args and args[0] == "roles":
        deploy_roles()
    elif args and args[0] == "global":
        deploy_global()
    else:
        deploy_roles()
        deploy_global()
    return ""


def deploy_roles():
    ''' Creates role assignments '''
    policy = Policy()
    if not policy.load():
        log.error(policy.error)
        return ""
    policy.expand()

    dsr = DeepSeaRoles(policy.yaml)
    dsr.invert()
    if not dsr.write():
        log.error(dsr.error)
        return ""

    dsc = DeepSeaCustom(policy.custom)
    if not dsc.write():
        log.error(dsc.error)
        return ""
    return ""


def deploy_global():
    ''' Creates initial global configuration '''
    dsg = DeepSeaGlobal()
    if dsg.absent():
        dsn = DeepSeaNetwork()
        if not dsn.scan():
            log.error(dsn.error)
            return ""

        dsg.networks(dsn.mgmt(), dsn.public(), dsn.cluster())
        if not dsg.write():
            log.error(dsg.error)
            return ""
    return ""


def distribute():
    ret = LocalClient().cmd(
        "cluster:ceph",
        'state.apply', ['ceph.configuration'],
        tgt_type='pillar')
    return evaluate_state_return(ret)


def create():
    ret = LocalClient().cmd(
        "roles:master",
        'state.apply', ['ceph.configuration.create'],
        tgt_type='pillar')
    return evaluate_state_return(ret)
