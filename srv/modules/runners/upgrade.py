# -*- coding: utf-8 -*-
# vim: ts=8 et sw=4 sts=4
# pylint: disable=modernize-parse-error
"""
Verify that an automated upgrade is possible
"""
from __future__ import absolute_import
from __future__ import print_function
import re
# pylint: disable=import-error,3rd-party-module-not-gated,redefined-builtin
import salt.client
import salt.utils.error
from packaging import version
import json
import yaml


class UpgradeValidation(object):
    """
    Due to the current situation you have to upgrade
    all monitors before ceph allows you to start any OSD
    Our current implementation of maintenance upgrades
    triggers this behavior if you happen to have
    Monitors and Storage roles assigned on the same node
    (And more then one monitor)
    To avoid this, before actually providing a proper solution,
    we stop users to execute the upgade in the first place.
    """

    def __init__(self, cluster='ceph'):
        """
        Initialize Salt client, cluster
        """
        self.local = salt.client.LocalClient()
        self.cluster = cluster

    def colocated_services(self):
        """
        Check for shared monitor and storage roles
        """
        search = "I@cluster:{}".format(self.cluster)
        pillar_data = self.local.cmd(
            search, 'pillar.items', [], tgt_type="compound")
        for host in pillar_data:
            if 'roles' in pillar_data[host]:
                if ('storage' in pillar_data[host]['roles']
                        and 'mon' in pillar_data[host]['roles']):
                    msg = """
                         ************** PLEASE READ ***************
                         We currently do not support upgrading when
                         you have a monitor and a storage role
                         assigned on the same node.
                         ******************************************"""
                    return False, msg
        return True, ""

    def is_master_standalone(self):
        """
        Check for shared master and storage role
        """
        search = "I@roles:master"
        pillar_data = self.local.cmd(
            search, 'pillar.items', [], tgt_type="compound")
        # in case of multimaster
        for host in pillar_data:
            if 'roles' in pillar_data[host]:
                if 'storage' in pillar_data[host]:
                    msg = """
                         ************** PLEASE READ ***************
                         Detected a storage role on your master.
                         This is not supported. Please migrate all
                         OSDs off the master in order to continue.
                         ******************************************"""
                    return False, msg
        return True, ""

    @staticmethod
    def is_supported():
        """
        Check if the automated upgrade is supported
        """
        msg = """
                ************** PLEASE READ ***************
                The automated upgrade is currently not supported.
                Please refer to the official documentation.
                ******************************************"""
        return False, msg

    def deprecated_straw(self):
        """
        Check if the straw algorithm is still in use
        """
        search = "I@roles:master"
        algs = self.local.cmd(search, 'osd.alg', [], tgt_type="compound")
        result = list(algs.values())[0]
        if 'straw' in result:
            msg = """
                ************** PLEASE READ ***************
                The following buckets are configured using
                the deprecated straw algorithm.

                {}

                Run `ceph osd crush set-all-straw-buckets-to-straw2`
                ******************************************
                """.format(", ".join(result['straw']))
            return False, msg
        return True, ""


class OrigDriveGroup:

    def migrate(self, data, storage_hosts=[]):
        self.__setattr__('service_type', 'osd')
        self.__setattr__('filter_logic', 'OR')
        for name, spec in data.items():
            self.__setattr__('service_id', name)
            for k, v in spec.items():
                self.__setattr__(k, v, storage_hosts)

    def __setattr__(self, key, value, storage_hosts=[]):
        if key == 'format' and value not in ['bluestore']:
            raise Exception('Only <bluestore> is supported.')
        if key == 'target':
            if value == 'I@roles:storage':
                self.__dict__['placement'] = dict(hosts=storage_hosts)
            else:
                self.__dict__['placement'] = dict(host_pattern=value)
            return
        # more known restrictions & changes go here
        self.__dict__[key] = value

    def to_yaml(self):
        return yaml.safe_dump(self.__dict__)


def help_():
    """
    Usage
    """
    usage = (
        'salt-run upgrade.check:\n\n'
        '    Performs a series of checks to verify that upgrades are possible\n'
        '\n\n')
    print(usage)
    return ""


def check():
    """
    Run upgrade checks
    """
    uvo = UpgradeValidation()
    checks = [uvo.is_master_standalone,
              uvo.is_supported,
              uvo.deprecated_straw]  # , uvo.colocated_services]
    for chk in checks:
        ret, msg = chk()
        if not ret:
            print(msg)
            return ret
    return ret


def _sort_nodes_by_role(nodes, roles):
    """
    Given a list of nodes, return the list sorted first by role in upgrade order
    (master, then mon/mgr, then mds, then storage, ...), and secondly by name.

    The roles parameter is a dict mapping _all_ node names to a list of their
    assigned roles (i.e. `salt '*' pillar.get roles`), so that this function can
    actually figure out what roles are assigned to each node in the nodes list.
    """
    nodes_sorted = []
    for role in ['master', 'mon', 'mgr', 'storage', 'mds', 'rgw', 'igw', 'ganesha']:
        role_nodes = [node for node in roles if role in roles[node] and node in nodes]
        role_nodes.sort()
        nodes_sorted.extend([node for node in role_nodes if node not in nodes_sorted])
    return nodes_sorted


def _print_nodes_to_upgrade(releases, newest, roles):
    """
    Prints a list of nodes currently on the newest release, followed by an ordered
    list of which nodes need upgrading next.

    releases is a dict mapping node names to software versions
    newest is the newest installed version
    roles is a dict as used by _sort_nodes_by_role()
    """
    upgraded_nodes = _sort_nodes_by_role([node for node in releases if releases[node] == newest],
                                         roles)
    nodes_to_upgrade = _sort_nodes_by_role([node for node in releases if releases[node] < newest],
                                           roles)

    print("Nodes running these software versions:")
    for node in upgraded_nodes:
        print("  {} (assigned roles: {})".format(node, ", ".join(roles[node])))
    print("")

    print("Nodes running older software versions must be upgraded in the following order:")
    i = 1
    for node in nodes_to_upgrade:
        print("{:4}: {} (assigned roles: {})".format(i, node, ", ".join(roles[node])))
        i += 1
    print("")


def status():
    """
    Check status of upgrade.  This is similar to status.report, but if the
    base OS version or ceph version isn't identical on all nodes, it will
    advise which node(s) should be upgraded next.
    """
    __opts__ = salt.config.client_config('/etc/salt/master')
    __grains__ = salt.loader.grains(__opts__)
    __opts__['grains'] = __grains__
    __utils__ = salt.loader.utils(__opts__)
    __salt__ = salt.loader.minion_mods(__opts__, utils=__utils__)
    master_minion = __salt__['master.minion']()

    local = salt.client.LocalClient()

    # os_codename and ceph_version are pretty strings, e.g.:
    # - SUSE Linux Enterprise Server 15 SP1
    # - ceph version 14.2.1-468-g994fd9e0cc (994fd9e0cc[...]) nautilus (stable)
    # (Unless a node is down, in which case they'll be "Unknown (node down?)"
    # or "Not installed" if Ceph is not installed yet)
    os_codename, _, ceph_version = __utils__['status.get_sys_versions']()

    # Following is possibly a slightly obscure test.  We want to run a bunch of pre-upgrade
    # checks when upgrading from SES6->7, but, this upgrade runner could also be invoked
    # on a system which is part way through a SES5->6 upgrade, in which case some nodes
    # would be SLE 12 SP3 and some would be SLE 15 SP1.  So, we check if there's any oses
    # that aren't a variant on SLE 15 (or are down/Unkown).  If the list is empty, we
    # assume we're on a SLE 15 SP1 or SP2 base, and can sensibly run the SES6->7 checks.
    non_sle_15 = [os for os in set(os_codename.values())
                    if not os.startswith("SUSE Linux Enterprise Server 15")
                    and not os.startswith("Unknown")]
    if len(non_sle_15) == 0:
        require_osd_release = list(local.cmd(master_minion, 'osd.require_osd_release', []).items())[0][1]
        if require_osd_release[0] < 'n':
            print("'require-osd-release' is currently '{}', but must be set to 'nautilus'".format(require_osd_release))
            print("before upgrading to SES 7.  Please run `ceph osd require-osd-release nautilus`")
            print("to fix this before proceeding further.")
            print("")

        filestore_osds = list(local.cmd(master_minion, 'cmd.run',
            ["ceph osd metadata | jq '.[] | select(.osd_objectstore == \"filestore\") | .id'"]).items())[0][1].split()
        if filestore_osds:
            print("The following OSDs are using FileStore:")
            print("  {}".format(', '.join(filestore_osds)))
            print("All FileStore OSDs must be converted to BlueStore before upgrading to SES 7.")
            print("")

        filesystems = list(local.cmd(master_minion, 'cmd.run',
            ["ceph fs ls --format=json|jq -r '.[][\"name\"]'"]).items())[0][1].split()
        if filesystems:
            for fs in filesystems:
                max_mds = int(list(local.cmd(master_minion, 'cmd.run',
                    ["ceph fs get {}|awk '/max_mds/ {{print $2}}'".format(fs)]).items())[0][1])
                if max_mds > 1:
                    print("The '{}' filesystem has {} MDS daemons.".format(fs, max_mds))
                    print("Before upgrading MDS daemons, reduce the number of ranks to 1 by running")
                    print("`ceph fs set {} max_mds 1`".format(fs))
                    print("")
            up_standbys = int(list(local.cmd(master_minion, 'cmd.run',
                ["ceph status --format=json-pretty|jq -r '.[\"fsmap\"][\"up:standby\"]'"]).items())[0][1])
            if up_standbys > 0:
                if up_standbys > 1:
                    print("There are {} standby MDS daemons running.".format(up_standbys))
                else:
                    print("There is 1 standby MDS daemon running.")
                print("All standby MDS daemons must to be stopped prior to upgrading them.")
                print("")

    if len(set(os_codename.values())) == 1 and len(set(ceph_version.values())) == 1:
        # OS version and ceph version are the same across the whole cluster
        print("All nodes are running:")
        print("  ceph: {}".format(next(iter(ceph_version.values()))))
        print("  os: {}".format(next(iter(os_codename.values()))))
        print("")
        return ""

    # We've got different versions of base OS, or ceph, or both, so we need:
    # - all the roles, to provide advice on what next to upgrade
    # - the OS and ceph versions in an easily comparable form, to figure out
    #   what's newest

    down_nodes = [node for node in os_codename if os_codename[node].startswith("Unknown")]

    search = "I@cluster:ceph"
    if down_nodes:
        search += " and not ( {} )".format("or ".join(down_nodes))

    roles = local.cmd(search, 'pillar.get', ['roles'], tgt_type="compound")

    os_release = local.cmd(search, 'grains.get', ['osrelease'], tgt_type="compound")
    for node in os_release:
        os_release[node] = version.parse(os_release[node])

    ceph_release = {}
    for node in ceph_version:
        match = re.match(r'ceph version ([^\s]+)', ceph_version[node])
        if match:
            ceph_release[node] = version.parse(match.group(1))
        else:
            # If ceph_version is "Unknown" or "Not installed", this still gives
            # a comparable version object, which sorts before actual versions
            ceph_release[node] = version.parse(ceph_version[node])

    # this max trick gives us the dict key of some host with the highest
    # version, so we can use that to extract the pretty string from os_codename
    # or ceph_version for display
    newest_os = max(os_release, key=os_release.get)
    newest_ceph = max(ceph_release, key=ceph_release.get)

    print("The newest installed software versions are:")
    print("  ceph: {}".format(ceph_version[newest_ceph]))
    print("  os: {}".format(os_codename[newest_os]))
    print("")

    if len(set(os_codename.values())) > 1:
        # If there's more than one operating system present, use the OS version as the
        # basis for what to upgrade...
        _print_nodes_to_upgrade(os_release, os_release[newest_os], roles)
    else:
        # ...otherwise, it's just the ceph version we care about
        _print_nodes_to_upgrade(ceph_release, ceph_release[newest_ceph], roles)

    if down_nodes:
        print("Unable to contact these nodes (node down or Salt minion inactive?):")
        for node in down_nodes:
            print("  {}".format(node))
        print("")

    return ""


def ceph_salt_config():
    """
    Generate minimal JSON suitable for import into ceph-salt, based on DeepSea
    configration.
    Call via `salt-run upgrade.ceph_salt_config > ceph-salt-config.json`
    """
    config = {
        'minions': {
            'all': [],
            'admin': [],
            'cephadm': []
        },
        'bootstrap_minion': None,
        'bootstrap_mon_ip': None,
        'container': {
            'registries_enabled': True,
            'registries': [],
            'images': {
                'ceph': 'registry.suse.com/ses/7/ceph/ceph'
            }
        },
        'dashboard': {
            # These values are just so the display gives an indication of what's
            # really going to happen when the user runs `ceph-salt config ls`
            # (the dashboard won't be reconfigured during an upgrade)
            'username': 'USE EXISTING',
            'password': 'USE EXISTING',
            'password_update_required': False
        },
        'time_server': {
            'enabled': True,
            'external_time_servers': ['pool.ntp.org'],
        }
    }

    __opts__ = salt.config.client_config('/etc/salt/master')
    __grains__ = salt.loader.grains(__opts__)
    __opts__['grains'] = __grains__
    __utils__ = salt.loader.utils(__opts__)
    __salt__ = salt.loader.minion_mods(__opts__, utils=__utils__)
    master_minion = __salt__['master.minion']()

    runner = salt.runner.RunnerClient(__opts__)
    mon_ips = dict(runner.cmd('select.public_addresses',
                              ['cluster=ceph', 'roles=mon', 'tuples=True'], print_event=False))

    local = salt.client.LocalClient()
    roles = local.cmd("I@cluster:ceph", 'pillar.get', ['roles'], tgt_type="compound")

    for node in sorted(roles):
        config['minions']['all'].append(node)
        config['minions']['cephadm'].append(node)
        if 'master' in roles[node] or 'admin' in roles[node]:
            config['minions']['admin'].append(node)
        if not config['bootstrap_minion'] and 'mon' in roles[node]:
            config['bootstrap_minion'] = node
            config['bootstrap_mon_ip'] = mon_ips[node]

    if list(local.cmd(master_minion, 'pillar.get', ['time_init']).items())[0][1] == "disabled":
        config['time_server']['enabled'] = False
    else:
        time_server = list(local.cmd(master_minion, 'pillar.get', ['time_server']).items())[0][1]
        if type(time_server) is list:
            # This is a bit sketchy, but ceph-salt currently (2020-09-23)
            # only allows single time servers, and in any case the user still
            # has to review the ceph-salt config before applying it.
            time_server = time_server[0]
        config['time_server']['server_host'] = time_server

    container_image = list(
        local.cmd(master_minion, 'pillar.get', ['ses7_container_image']).items())[0][1]
    if container_image:
        config['container']['images']['ceph'] = container_image

    container_registries = list(
        local.cmd(master_minion, 'pillar.get', ['ses7_container_registries']).items())[0][1]
    if container_registries:
        config['container']['registries'] = container_registries

    return json.dumps(config, indent=4)


def generate_service_specs():
    """
    Generate service specs suitable for applying to the ceph orchestrator,
    based on DeepSea configuration.  This includes mon, mgr, osd, crash,
    node-exporter, prometheus, grafana and alertmanager.
    Call via `salt-run upgrade.generate_service_specs > specs.yaml`
    """

    __opts__ = salt.config.client_config('/etc/salt/master')
    __grains__ = salt.loader.grains(__opts__)
    __opts__['grains'] = __grains__
    __utils__ = salt.loader.utils(__opts__)
    __salt__ = salt.loader.minion_mods(__opts__, utils=__utils__)

    # There's always a crash daemon (previously deployed automatically by ceph)
    # and node exporter (deployed automatically by deepsea on all nodes)
    service_specs = [
        {
            'service_type': 'crash',
            'placement': {
                'host_pattern': '*'
            }
        },
        {
            'service_type': 'node-exporter',
            'placement': {
                'host_pattern': '*'
            }
        }
    ]

    local = salt.client.LocalClient()
    roles = local.cmd("I@cluster:ceph", 'pillar.get', ['roles'], tgt_type="compound")

    # Lifted from srv/modules/runners/select.py
    def _grain_host(client, minion):
        return list(client.cmd(minion, 'grains.item', ['host']).values())[0]['host']

    for service_type in ['mon', 'mgr', 'prometheus', 'grafana']:
        hosts = [_grain_host(local, node) for node in roles if service_type in roles[node]]
        if not hosts:
            # It's possible (although unlikely) that some roles don't exist, thus match
            # no hosts.  In this case, there's no point generating a service spec.
            continue
        hosts.sort()
        service_specs.append({
            'service_type': service_type,
            'placement': {
                'hosts': hosts
            }
        })
        # Irritating special case to handle alertmanager, which DS configures to run
        # on the same host(s) as prometheus by default
        if service_type == 'prometheus':
            service_specs.append({
                'service_type': 'alertmanager',
                'placement': {
                    'hosts': hosts
                }
            })

    storage_hosts = [_grain_host(local, node) for node in roles if 'storage' in roles[node]];
    with open('/srv/salt/ceph/configuration/files/drive_groups.yml', 'r') as fd:
        for dg in yaml.safe_load_all(fd):
            dg_o = OrigDriveGroup()
            dg_o.migrate(dg, storage_hosts)
            service_specs.append(dg_o.__dict__)

    return "\n---\n".join(yaml.safe_dump(service).strip() for service in service_specs)


__func_alias__ = {
    'help_': 'help',
}
