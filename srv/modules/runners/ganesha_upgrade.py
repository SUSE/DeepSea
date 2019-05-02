# -*- coding: utf-8 -*-
"""
NFS-Ganesha Upgrade script
"""
# pylint: disable=import-error,3rd-party-module-not-gated,redefined-builtin
# pylint: disable=broad-except,too-many-return-statements,unused-argument
from __future__ import absolute_import

from collections import defaultdict
import logging
import yaml

import salt.client
import salt.config
import salt.loader
from salt.ext.six.moves import range


log = logging.getLogger(__name__)


# pylint: disable=missing-docstring
class GaneshaConfParser(object):
    def __init__(self, raw_config):
        self.pos = 0
        self.text = ""
        self.clean_config(raw_config)

    def clean_config(self, raw_config):
        for line in raw_config.split("\n"):
            cardinal_idx = line.find('#')
            if cardinal_idx == -1:
                self.text += line
            else:
                # remove comments
                self.text += line[:cardinal_idx]
            if line.startswith("%"):
                self.text += "\n"

    def remove_all_whitespaces(self):
        new_text = ""
        in_string = False
        in_section = False
        for i, cha in enumerate(self.text):
            log.debug("RAW: [%s, %s] i=%s prev=%s curr=%s", in_section,
                      in_string, i, self.text[i-1], cha)
            if in_section:
                if cha == '\n':
                    new_text += cha
                    in_section = False
                elif i == (len(self.text)-1):
                    if cha != '"' and self.text[i-1] != '\\':
                        new_text += cha
                    in_section = False
                elif cha != '"' and self.text[i-1] != '\\':
                    new_text += cha
            elif not in_section and (i == 0 or self.text[i-1] in ['\n', '}']) and cha == '%':
                in_section = True
                new_text += cha
            elif in_string or cha not in [' ', '\n', '\t']:
                new_text += cha
            if cha == '"' and self.text[i-1] != '\\':
                in_string = not in_string
        self.text = new_text

    def raise_exception(self, msg):
        raise Exception("{}\n** Parsed **\n{}\n** Remaining **\n{}"
                        .format(msg, self.text[:self.pos], self.stream()))

    def stream(self):
        return self.text[self.pos:]

    def parse_block_name(self):
        idx = self.stream().find('{')
        if idx == -1:
            self.raise_exception("Cannot find block name")
        block_name = self.stream()[:idx]
        self.pos += idx+1
        return block_name

    def parse_block_or_section(self):
        if self.stream().startswith("%url "):
            # section line
            self.pos += 5
            idx = self.stream().find('\n')
            if idx == -1:
                value = self.stream()
                self.pos += len(self.stream())
            else:
                value = self.stream()[:idx]
                self.pos += idx+1
            block_dict = {'block_name': '%url', 'value': value}
            return block_dict

        block_name = self.parse_block_name().upper()
        block_dict = {'block_name': block_name}
        self.parse_block_body(block_dict)
        if self.stream()[0] != '}':
            self.raise_exception("No closing bracket '}' found at the end of block")
        self.pos += 1
        return block_dict

    def parse_parameter_value(self, raw_value):
        colon_idx = raw_value.find(',')

        if colon_idx == -1:
            try:
                return int(raw_value)
            except ValueError:
                if raw_value == "true":
                    return True
                if raw_value == "false":
                    return False
                if raw_value.find('"') == 0:
                    return raw_value[1:-1]
                return raw_value
        else:
            return [self.parse_parameter_value(v.strip())
                    for v in raw_value.split(',')]

    def parse_stanza(self, block_dict):
        equal_idx = self.stream().find('=')
        semicolon_idx = self.stream().find(';')
        if equal_idx == -1:
            self.raise_exception("Malformed stanza: no equal symbol found.")
        parameter_name = self.stream()[:equal_idx].lower()
        parameter_value = self.stream()[equal_idx+1:semicolon_idx]
        block_dict[parameter_name] = self.parse_parameter_value(
            parameter_value)
        self.pos += semicolon_idx+1

    def parse_block_body(self, block_dict):
        last_pos = self.pos
        while True:
            semicolon_idx = self.stream().find(';')
            lbracket_idx = self.stream().find('{')
            rbracket_idx = self.stream().find('}')

            if rbracket_idx == 0:
                # block end
                return

            if (semicolon_idx != -1 and lbracket_idx != -1
                    and semicolon_idx < lbracket_idx) \
                    or (semicolon_idx != -1 and lbracket_idx == -1):
                self.parse_stanza(block_dict)
            elif (semicolon_idx != -1 and lbracket_idx != -1
                  and semicolon_idx > lbracket_idx) or (
                      semicolon_idx == -1 and lbracket_idx != -1):
                if '_blocks_' not in block_dict:
                    block_dict['_blocks_'] = []
                block_dict['_blocks_'].append(self.parse_block_or_section())
            else:
                self.raise_exception("Malformed stanza: no semicolon found.")

            if last_pos == self.pos:
                self.raise_exception("Infinite loop while parsing block content")
            last_pos = self.pos

    def parse(self):
        self.remove_all_whitespaces()
        blocks = []
        while self.stream():
            block_dict = self.parse_block_or_section()
            blocks.append(block_dict)
        return blocks

    @staticmethod
    def _indentation(depth, size=4):
        conf_str = ""
        for _ in range(0, depth*size):
            conf_str += " "
        return conf_str

    @staticmethod
    def write_block_body(block, depth=0):
        def format_val(key, val):
            if isinstance(val, list):
                return ', '.join([format_val(key, v) for v in val])
            if isinstance(val, bool):
                return str(val).lower()
            if isinstance(val, int) or (block['block_name'] == 'CLIENT'
                                        and key == 'clients'):
                return '{}'.format(val)
            return '"{}"'.format(val)

        conf_str = ""
        for key, val in block.items():
            if key == 'block_name':
                continue
            elif key == '_blocks_':
                for blo in val:
                    conf_str += GaneshaConfParser.write_block(blo, depth)
            elif val:
                conf_str += GaneshaConfParser._indentation(depth)
                conf_str += '{} = {};\n'.format(key, format_val(key, val))
        return conf_str

    @staticmethod
    def write_block(block, depth):
        if block['block_name'] == "%url":
            return '%url "{}"\n\n'.format(block['value'])

        conf_str = ""
        conf_str += GaneshaConfParser._indentation(depth)
        conf_str += format(block['block_name'])
        conf_str += " {\n"
        conf_str += GaneshaConfParser.write_block_body(block, depth+1)
        conf_str += GaneshaConfParser._indentation(depth)
        conf_str += "}\n\n"
        return conf_str

    @staticmethod
    def write_conf(blocks):
        if not isinstance(blocks, list):
            blocks = [blocks]
        conf_str = ""
        for block in blocks:
            conf_str += GaneshaConfParser.write_block(block, 0)
        return conf_str


def _check_if_fresh_install(roles):
    local = salt.client.LocalClient()
    for role in roles:
        result = local.cmd('I@roles:{}'.format(role), 'pkg.info_installed',
                           tgt_type='compound')
        if not result:
            raise Exception("Failed to run pkg.info_installed in ganesha minions")

        for _, res in result.items():
            if isinstance(res, dict) and 'nfs-ganesha-ceph' in res:
                return False

    return True


def validate():
    """
    Validates some pre-conditions necessary for the successful completion of
    the upgrade process.
    """
    __opts__ = salt.config.client_config('/etc/salt/master')
    __grains__ = salt.loader.grains(__opts__)
    __opts__['grains'] = __grains__
    __utils__ = salt.loader.utils(__opts__)
    __salt__ = salt.loader.minion_mods(__opts__, utils=__utils__)

    roles = __salt__['pillar.get']('ganesha_configurations', ['ganesha'])

    try:
        if _check_if_fresh_install(roles):
            # don't do any validation, it's a fresh install
            return True
    except Exception as ex:
        __context__['retcode'] = 1
        return str(ex)

    master = __salt__['master.minion']()
    nfs_pool = __salt__['master.find_pool'](['cephfs', 'rgw'])

    if not nfs_pool:
        __context__['retcode'] = 1
        return False

    log.info("Checking RADOS rw access of '%s' pool in '%s'", nfs_pool, master)

    # verify cluster access (RW permission for RADOS objects)
    local = salt.client.LocalClient(mopts=__opts__)
    result = local.cmd(master, 'ganesha.validate_rados_rw', [nfs_pool])
    log.info("RADOS RW RESULT: %s", result)
    if not result:
        __context__['retcode'] = 1
        return "RADOS rw access failed"
    elif not isinstance(result[master], bool):
        __context__['retcode'] = 1
        return result[master]

    # verify that the set of minions associated with ganesha configuration
    # roles does not have repetitions
    local = salt.client.LocalClient()
    log.info("Found ganesha roles: %s", roles)
    minions = set()
    for role in roles:
        log.info("Issuing test.ping command to I@roles:%s", role)
        result = local.cmd('I@roles:{}'.format(role), 'test.ping',
                           tgt_type='compound')
        log.debug("RESULT: %s", result)
        for minion in result:
            if minion in minions:
                __context__['retcode'] = 1
                return "Minion {} is part of two different ganesha" \
                       " configurations".format(minion)
            minions.add(minion)

    # verify that nfs-ganesha configs are parsable
    for role in roles:
        minion_conf = local.cmd('I@roles:{}'.format(role), 'cmd.run',
                                ['cat /etc/ganesha/ganesha.conf'],
                                tgt_type='compound')
        for minion, raw_config in minion_conf.items():
            if "No such file" in raw_config:
                __context__['retcode'] = 1
                return "No /etc/ganesha/ganesha.conf file found in {}".format(minion)
            blocks = GaneshaConfParser(raw_config).parse()
            log.debug("Parsed '%s' nfs-ganesha configuration: %s", minion, blocks)
            if not blocks:
                __context__['retcode'] = 1
                return "Empty or unparsable NFS-Ganesha configuration"

    # verify that nfs-ganesha gateways are still running
    for role in roles:
        result = local.cmd('I@roles:{}'.format(role),
                           'ganesha.validate_ganesha_daemon', [],
                           tgt_type='compound')
        for minion, res in result.items():
            if not isinstance(res, bool):
                __context__['retcode'] = 1
                return res

    return True


def _compare_export_blocks(export1, export2):
    e_id1 = export1['export_id']
    e_id2 = export2['export_id']
    export1['export_id'] = 0
    export2['export_id'] = 0
    res = export1 == export2
    export1['export_id'] = e_id1
    export2['export_id'] = e_id2
    return res


def upgrade(**kwargs):
    """
    This procedure will upgrade each gateway sequentially.
    """

    __opts__ = salt.config.client_config('/etc/salt/master')
    __grains__ = salt.loader.grains(__opts__)
    __opts__['grains'] = __grains__
    __utils__ = salt.loader.utils(__opts__)
    __salt__ = salt.loader.minion_mods(__opts__, utils=__utils__)

    roles = __salt__['pillar.get']('ganesha_configurations', ['ganesha'])
    try:
        if _check_if_fresh_install(roles):
            # don't do upgrade, it's a fresh install
            return True
    except Exception as ex:
        __context__['retcode'] = 1
        return str(ex)

    master = __salt__['master.minion']()
    nfs_pool = __salt__['master.find_pool'](['cephfs', 'rgw'])

    local = salt.client.LocalClient()

    raw_configs = {}
    for role in roles:
        minion_conf = local.cmd('I@roles:{}'.format(role), 'cmd.run',
                                ['cat /etc/ganesha/ganesha.conf'],
                                tgt_type='compound')
        raw_configs.update(minion_conf)

    daemon_config = {}
    export_blocks = []
    minion_to_daemon_id = {}

    for minion, raw_config in sorted([(k, v) for k, v in raw_configs.items()], key=lambda v: v[0]):
        daemon_id = local.cmd(minion, 'grains.get', ['host'])[minion]
        minion_to_daemon_id[minion] = daemon_id
        blocks = GaneshaConfParser(raw_config).parse()
        daemon_config[daemon_id] = blocks
        export_blocks.extend([(b, daemon_id) for b in blocks if b['block_name'] == 'EXPORT'])

    unique_export_blocks = []
    export_count = 1
    for export_block, daemon_id in export_blocks:
        duplicate = [(e, d) for e, d in unique_export_blocks
                     if _compare_export_blocks(e, export_block)]
        if duplicate:
            if len(duplicate) > 1:
                __context__['retcode'] = 1
                return "Fatal error: found more than 1 duplicate export"
            _, dup = duplicate[0]
            dup.append(daemon_id)
        else:
            export_block['export_id'] = export_count
            export_count += 1
            unique_export_blocks.append((export_block, [daemon_id]))

    log.info("Export list: %s", unique_export_blocks)

    # write each export to its own RADOS object
    for export_block, _ in unique_export_blocks:
        raw_config = GaneshaConfParser.write_conf([export_block])
        res = local.cmd(master, 'ganesha.write_object',
                        [nfs_pool, "export-{}".format(export_block['export_id']),
                         raw_config])
        if not res:
            __context__['retcode'] = 1
            return "Failed to write export (id={}) object" \
                   .format(export_block['export_id'])
        if res and isinstance(res[master], bool) and not res[master]:
            __context__['retcode'] = 1
            return "Failed to write export (id={}) object: export" \
                   " object already exists".format(export_block['export_id'])
        if res and res[master] is not True:
            __context__['retcode'] = 1
            return "Failed to write export (id={}) object:\n{}" \
                   .format(export_block['export_id'], res[master])

    log.info("NFS-Ganesha export objects created")

    exports_per_daemon = defaultdict(list)
    for export_block, daemons in unique_export_blocks:
        for daemon_id in daemons:
            exports_per_daemon[daemon_id].append(export_block['export_id'])

    log.info("Exports per daemon: %s", exports_per_daemon)

    # write each daemon config to its own RADOS object
    for daemon_id, exports in exports_per_daemon.items():
        blocks = []
        for export_id in exports:
            blocks.append({
                'block_name': "%url",
                'value': "rados://{}/ganesha/export-{}"
                         .format(nfs_pool, export_id)
            })
        raw_config = GaneshaConfParser.write_conf(blocks)
        res = local.cmd(master, 'ganesha.write_object',
                        [nfs_pool, "conf-{}".format(daemon_id), raw_config])
        if not res:
            __context__['retcode'] = 1
            return "Failed to write daemon config (id={}) object" \
                   .format(daemon_id)
        if res and isinstance(res[master], bool) and not res[master]:
            __context__['retcode'] = 1
            return "Failed to write daemon config (id={}) object: config" \
                   " object already exists".format(daemon_id)
        if res and res[master] is not True:
            __context__['retcode'] = 1
            return "Failed to write daemon config (id={}) object:\n{}" \
                   .format(daemon_id, res[master])

    # clean pillar ganesha_config override
    filename = '/srv/pillar/ceph/stack/ceph/cluster.yml'
    contents = {}
    with open(filename, 'r') as yml:
        contents = yaml.safe_load(yml)
        if not contents:
            contents = {}
    if 'ganesha_config' in contents:
        del contents['ganesha_config']
        friendly_dumper = yaml.SafeDumper
        friendly_dumper.ignore_aliases = lambda self, data: True
        with open(filename, 'w') as yml:
            yml.write(yaml.dump(contents,
                                Dumper=friendly_dumper,
                                default_flow_style=False))
    # refresh pillar
    local.cmd(master, 'saltutils.pillar_refresh')

    # backup config files
    for role in roles:
        result = local.cmd("I@roles:{}".format(role),
                           "ganesha.backup_config_file",
                           ["/etc/ganesha/ganesha.conf"],
                           tgt_type="compound")
        if not result:
            __context__['retcode'] = 1
            return "Failed to backup ganesha.conf from role '{}'".format(role)
        for minion, res in result.items():
            if not isinstance(res, bool):
                __context__['retcode'] = 1
                return res

            if res is False:
                log.warning("backup of /etc/ganesha/ganesha.conf ignored in %s"
                            " as a backup already existed", minion)

            conf_file = "/srv/salt/ceph/ganesha/cache/{}.{}.conf" \
                        .format(role, minion_to_daemon_id[minion])
            res = local.cmd(master, "ganesha.backup_config_file",
                            [conf_file])
            if not res:
                __context__['retcode'] = 1
                return "Failed to backup cache ganesha.conf from role '{}'" \
                       .format(role)
            if not isinstance(res[master], bool):
                __context__['retcode'] = 1
                return res[master]
            if res[master] is False:
                log.warning("backup of % ignored as a backup already existed",
                            conf_file)

    # set grains for forcing daemons to restart
    if export_blocks:
        for role in roles:
            result = local.cmd("I@roles:{}".format(role), "grains.set",
                               ["restart_{}".format(role), True],
                               tgt_type="compound")
            if not result:
                __context__['retcode'] = 1
                return "Failed to set restart grains."
            for minion, res in result.items():
                if not isinstance(res, dict):
                    __context__['retcode'] = 1
                    return "Failed to set restart grain in {}:\n{}" \
                           .format(minion, res)

    return True
