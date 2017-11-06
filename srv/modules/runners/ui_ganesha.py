# -*- coding: utf-8 -*-
# pylint: disable=modernize-parse-error
#
# The salt-api calls functions with keywords that are not needed
# pylint: disable=unused-argument
"""
NFS Ganesha API runner

This runner provides a set of functions to get and save NFS-Ganesha
exports, supporting both CephFS and RGW FSALs.
This module also suports the deploy of the configured exports, as
well as, support for querying the status of Ganesha services and
exports.
"""

from __future__ import absolute_import
import json
import os
import salt.client
import yaml


class GaneshaConfParser(object):
    """
    Ganesha configuration file parser
    """

    def __init__(self, conf_file):
        """
        Load config file, initialize variables
        """
        self.pos = 0
        self.text = ""
        self.load_file(conf_file)

    def load_file(self, conf_file):
        """
        Read file without comments
        """
        with open(conf_file) as cfi:
            for line in cfi.readlines():
                cardinal_idx = line.find('#')
                if cardinal_idx == -1:
                    self.text += line
                else:
                    # remove comments
                    self.text += line[:cardinal_idx]

    def remove_all_whitespaces(self):
        """
        Strip whitespaces from lines
        """
        new_text = ""
        in_string = False
        for i, cha in enumerate(self.text):
            if in_string or cha not in [' ', '\n', '\t']:
                new_text += cha
            elif cha == '"' and self.text[i-1] != '\\':
                in_string = not in_string
        self.text = new_text

    def stream(self):
        """
        Return remaining file
        """
        return self.text[self.pos:]

    def parse_block_name(self):
        """
        Returns name of configuration block
        """
        idx = self.stream().find('{')
        if idx == -1:
            raise Exception("Cannot find block name")
        block_name = self.stream()[:idx]
        self.pos += idx+1
        return block_name

    def parse_block(self):
        """
        Parses curly brace block
        """
        block_name = self.parse_block_name().lower()
        block_dict = {'block_name': block_name}
        self.parse_block_body(block_dict)
        if self.stream()[0] != '}':
            raise Exception("No closing bracket '}' found at the end of block")
        self.pos += 1
        return block_dict

    def parse_parameter_value(self, raw_value):
        """
        Return value whether quoted or comma separated
        """
        colon_idx = raw_value.find(',')

        if colon_idx == -1:
            try:
                return int(raw_value)
            except ValueError:
                if raw_value.find('"') == 0:
                    return raw_value[1:-1]
                return raw_value
        else:
            return [self.parse_parameter_value(v.strip()) for v in raw_value.split(',')]

    def parse_stanza(self, block_dict):
        """
        Parse an individual line
        """
        equal_idx = self.stream().find('=')
        semicolon_idx = self.stream().find(';')
        if equal_idx == -1:
            raise Exception("Maformed stanza: no equal symbol found.")
        parameter_name = self.stream()[:equal_idx].lower()
        parameter_value = self.stream()[equal_idx+1:semicolon_idx]
        block_dict[parameter_name] = self.parse_parameter_value(parameter_value)
        self.pos += semicolon_idx+1

    def parse_block_body(self, block_dict):
        """
        Parse the whole body
        """
        last_pos = self.pos
        while True:
            semicolon_idx = self.stream().find(';')
            lbracket_idx = self.stream().find('{')
            rbracket_idx = self.stream().find('}')

            if rbracket_idx == 0:
                # block end
                return

            if ((semicolon_idx != -1 and
                 lbracket_idx != -1 and
                 semicolon_idx < lbracket_idx) or
                (semicolon_idx != -1 and
                 lbracket_idx == -1)):
                self.parse_stanza(block_dict)
            elif (semicolon_idx != -1 and lbracket_idx != -1 and semicolon_idx > lbracket_idx) or (
                  semicolon_idx == -1 and lbracket_idx != -1):
                if '_blocks_' not in block_dict:
                    block_dict['_blocks_'] = []
                block_dict['_blocks_'].append(self.parse_block())
            else:
                raise Exception("Malformed stanza: no semicolon found.")

            if last_pos == self.pos:
                raise Exception("Infinite loop while parsing block content")
            last_pos = self.pos

    def parse(self):
        """
        The general parser that returns blocks of configuration
        """
        self.remove_all_whitespaces()
        blocks = []
        while self.stream():
            block_dict = self.parse_block()
            blocks.append(block_dict)
        return blocks

    @staticmethod
    def _indentation(depth, size=4):
        """
        Prepend spaces to indent as necessary
        """
        conf_str = ""
        for _ in range(0, depth*size):
            conf_str += " "
        return conf_str

    @staticmethod
    def write_block_body(block, depth=0):
        """
        Return the block body
        """
        def format_val(key, val):
            """
            Return a comma separated list, raw value or quoted value
            """
            if isinstance(val, list):
                return ', '.join([format_val(key, v) for v in val])
            elif isinstance(val, int) or (block['block_name'] == 'CLIENT' and key == 'clients'):
                return '{}'.format(val)
            else:
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
        """
        Return the configuration block
        """
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
        """
        Return the configuration file
        """
        conf_str = ""
        for block in blocks:
            conf_str += GaneshaConfParser.write_block(block, 0)
        return conf_str


class Ganesha(object):
    """
    Ganesha specific configuration operations
    """
    @staticmethod
    def _process_ganesha_conf_block(block):
        """
        Extract attributes from configuration block
        """
        new_block = {}
        for key, val in block.items():
            if key in ['secret_access_key', 'access_key_id', 'block_name']:
                continue
            if 'name' in block and block['name'] == 'CEPH' and key == 'user_id':
                continue
            if key == '_blocks_':
                for blo in val:
                    if blo['block_name'] == 'fsal':
                        new_block['fsal'] = Ganesha._process_ganesha_conf_block(blo)
                    elif blo['block_name'] == 'client':
                        if 'client_blocks' not in new_block:
                            new_block['client_blocks'] = []
                        new_block['client_blocks'].append(
                            Ganesha._process_ganesha_conf_block(blo))
                continue
            new_block[key] = val
        return new_block

    @staticmethod
    def _process_ganesha_conf(conf):
        """
        Process configuration blocks that are not export
        """
        filtered_conf = []
        for block in conf:
            if block['block_name'] != 'export':
                continue
            filtered_conf.append(Ganesha._process_ganesha_conf_block(block))
        return filtered_conf

    @staticmethod
    def call_salt_module(local_client, role, fun, args, only_vals=True, minion=False):
        """
        Wrapper for Salt module since multiple values may be returned
        """
        target = "I@roles:{}".format(role) if not minion else role
        result = local_client.cmd(target, fun, args, expr_form="compound")
        if minion:
            return result[role]
        return [val for _, val in result.items()] if only_vals else result

    @staticmethod
    def get_exports():
        """
        Reads and parses the existing ganesha configuration files for each
        minion with the "ganesha" role.
        """
        local = salt.client.LocalClient()
        ganesha_hosts = Ganesha.call_salt_module(local, 'ganesha', 'grains.item', ['host', 'id'])
        result = []
        for host_id in ganesha_hosts:
            filename = "/srv/salt/ceph/ganesha/cache/ganesha.{}.conf".format(host_id['host'])
            if os.path.exists(filename):
                parser = GaneshaConfParser(filename)
                result.append({
                    'host': host_id['id'],
                    'exports': Ganesha._process_ganesha_conf(parser.parse())
                })
            else:
                result.append({
                    'host': host_id['id'],
                    'exports': []
                })
        return result

    @staticmethod
    # pylint: disable=too-many-return-statements
    def _add_secrets_to_exports(exports, local_client):
        """
        Add the users to the CEPH and RGW sections
        """
        for host_exports in exports:
            found_rgw_fsal = False
            if 'host' not in host_exports:
                return {'success': False, 'message': 'Bad format: host identifier is missing'}
            if 'exports' not in host_exports:
                return {'success': False, 'message': 'Bad format: host "exports" list is missing'}
            short_host = Ganesha.call_salt_module(local_client, host_exports['host'],
                                                  'grains.get', ['host'], minion=True)
            for export in host_exports['exports']:
                export['block_name'] = 'EXPORT'
                if 'fsal' not in export:
                    return {'success': False, 'message': 'Bad format: "fsal" block is missing'}
                fsal = export['fsal']
                fsal['block_name'] = 'FSAL'
                if 'name' not in fsal:
                    return {'success': False, 'message': 'Bad format: FSAL "name" is missing'}
                if fsal['name'] == 'CEPH':
                    fsal['user_id'] = 'ganesha.{}'.format(short_host)
                    keyring_filename = Ganesha.call_salt_module(local_client, 'master',
                                                                'keyring.file',
                                                                ['ganesha',
                                                                 'client.{}'
                                                                 .format(fsal['user_id'])])[0]
                    key = Ganesha.call_salt_module(local_client, 'master', 'keyring.secret',
                                                   [keyring_filename])[0]
                    fsal['secret_access_key'] = key
                elif fsal['name'] == 'RGW':
                    found_rgw_fsal = True
                    if 'user_id' not in fsal:
                        return {'success': False,
                                'message': 'Bad format: FSAL RGW "user_id" is missing'}
                    if 'access_key_id' not in fsal:
                        fsal['access_key_id'] = Ganesha.call_salt_module(local_client,
                                                                         'master',
                                                                         'rgw.access_key',
                                                                         [fsal['user_id']])[0]
                        if fsal['access_key_id'] is None:
                            return {'success': False,
                                    'message': 'FSAL RGW user_id "{}" does not exist'
                                               .format(fsal['user_id'])}
                    if 'secret_access_key' not in fsal:
                        fsal['secret_access_key'] = Ganesha.call_salt_module(
                            local_client, 'master', 'rgw.secret_key', [fsal['user_id']])[0]
                        if fsal['secret_access_key'] is None:
                            return {'success': False,
                                    'message': 'FSAL RGW user_id "{}" does not exist'
                                               .format(fsal['user_id'])}
            if found_rgw_fsal:
                host_exports['exports'].append({
                    'block_name': 'RGW',
                    'ceph_conf': '/etc/ceph/ceph.conf',
                    'name': 'client.ganesha.{}'.format(short_host),
                    'cluster': 'ceph'
                })
        return {'success': True}

    @staticmethod
    def _process_export_blocks(exports):
        """
        Process export blocks separately
        """
        for host_exports in exports:
            for export in host_exports['exports']:
                if export['block_name'] == 'EXPORT':
                    blocks = [export['fsal']]
                    export.pop('fsal')
                    if 'client_blocks' in export:
                        for client_block in export['client_blocks']:
                            client_block['block_name'] = 'CLIENT'
                            blocks.append(client_block)
                        export.pop('client_blocks')
                    export['_blocks_'] = blocks

    @staticmethod
    def _set_ganesha_config(local_client):
        """
        Add ganesha_config to cluster.yml

        Comments are removed from cluster.yml
        """

        filename = '/srv/pillar/ceph/stack/ceph/cluster.yml'
        contents = {}
        with open(filename, 'r') as yml:
            contents = yaml.safe_load(yml)
            if not contents:
                contents = {}
        contents['ganesha_config'] = 'default-ui'
        friendly_dumper = yaml.SafeDumper
        friendly_dumper.ignore_aliases = lambda self, data: True
        with open(filename, 'w') as yml:
            yml.write(yaml.dump(contents,
                                Dumper=friendly_dumper,
                                default_flow_style=False))
        # refresh pillar
        local_client.cmd("I@roles:master", 'saltutils.pillar_refresh', [''], expr_form="compound")

    @staticmethod
    def save_exports(exports):
        """
        Save the ganesha configuration for each gateway
        """
        if exports is None:
            return {'success': False, 'message': 'No exports config provided'}
        elif not isinstance(exports, list):
            return {'success': False, 'message': 'Bad format: exports is not an array'}

        local = salt.client.LocalClient()
        result = Ganesha._add_secrets_to_exports(exports, local)
        if not result['success']:
            return result
        Ganesha._process_export_blocks(exports)

        Ganesha._set_ganesha_config(local)

        for host_exports in exports:
            host = host_exports['host']
            try:
                short_host = Ganesha.call_salt_module(local, host, 'grains.get', ['host'],
                                                      minion=True)
                with open("/srv/salt/ceph/ganesha/cache/ganesha.{}.conf"
                          .format(short_host), 'w') as conf:
                    conf.write(GaneshaConfParser.write_conf(host_exports['exports']))
            except IOError as ex:
                return {'success': False, 'message': str(ex)}

        return {'success': True}

    @staticmethod
    def deploy_exports(minion=None):
        """
        Call 'salt <target> state.apply ceph.ganesha'
        """
        local = salt.client.LocalClient()
        master_minion = Ganesha.call_salt_module(
            local, 'master', 'pillar.get', ['master_minion'])[0]
        Ganesha.call_salt_module(local, master_minion, 'state.apply',
                                 ['ceph.ganesha.auth'], minion=True)
        if not minion:
            roles = Ganesha.call_salt_module(
                local, 'master', 'pillar.get', ['ganesha_configurations'])[0]
            if not roles:
                roles = ['ganesha']
            for role in roles:
                Ganesha.call_salt_module(local, role, 'state.apply', ['ceph.ganesha'], False)
        else:
            Ganesha.call_salt_module(local, minion, 'state.apply',
                                     ['ceph.ganesha'], minion=True)

    @staticmethod
    def check_exports_status():
        """
        Check the status of each export
        """
        exports = Ganesha.get_exports()
        local = salt.client.LocalClient()
        exports_info = Ganesha.call_salt_module(local, 'ganesha', 'ganesha.get_exports_info',
                                                [], False)
        result = {}
        for host_exports in exports:
            host = host_exports['host']
            if host not in exports_info or not exports_info[host]['success']:
                if host not in exports_info:
                    result[host] = {'active': False, 'message': 'nfs-ganesha service not running'}
                else:
                    result[host] = {'active': False, 'message': exports_info[host]['message']}
                continue

            result[host] = {'active': True, 'exports': []}
            for export in host_exports['exports']:
                found = False
                for export_info in exports_info[host]['exports']:
                    if export_info['export_id'] == export['export_id']:
                        result[host]['exports'].append({
                            'export_id': export['export_id'],
                            'active': export_info['active'],
                            'message': export_info['message'] if 'message' in export_info else None,
                        })
                        found = True
                        break
                if not found:
                    result[host]['exports'].append({
                        'export_id': export['export_id'],
                        'active': False,
                        'message': '{} is not exported'.format(
                            export['pseudo'] if 'pseudo' in export else export['path']),
                    })
        return result


def help_():
    """
    Usage
    """
    usage = ('salt-run ui_ganesha.get_hosts:\n\n'
             '    Returns the list of minions assigned the ganesha role\n'
             '\n\n'
             'salt-run ui_ganesha.get_fsals_available:\n\n'
             '    Returns a list of available backends\n'
             '\n\n'
             'salt-run ui_ganesha.get_exports:\n\n'
             '    Returns the list of NFS exports\n'
             '\n\n'
             'salt-run ui_ganesha.save_exports exports:\n\n'
             '    Saves the json formatted list of NFS exports\n'
             '\n\n'
             'salt-run ui_ganesha.deploy_exports:\n\n'
             '    Calls state.apply ceph.ganesha\n'
             '\n\n'
             'salt-run ui_ganesha.status_exports:\n\n'
             '    Returns status for each minion\n'
             '\n\n'
             'salt-run ui_ganesha.stop_exports:\n\n'
             '    Stops the ganesha service for each minion\n'
             '\n\n')
    print usage
    return ""


def get_hosts(**kwargs):
    """
    Returns the list of hosts that have the "ganesha" role
    """
    local = salt.client.LocalClient()
    return Ganesha.call_salt_module(local, 'ganesha', 'grains.get', ['id'])


def get_fsals_available(**kwargs):
    """
    Return the FileSystem Abstraction Layer types
    """
    # salt.saltutil.runner('select.minions', cluster='ceph', roles='mds')
    runner = salt.runner.RunnerClient(salt.config.client_config('/etc/salt/master'))
    result = []
    ret = runner.cmd('select.minions', ['cluster=ceph', 'roles=mds'], print_event=False)
    if ret:
        result.append('CEPH')
    ret = runner.cmd('select.minions', ['cluster=ceph', 'roles=rgw'], print_event=False)
    if ret:
        result.append('RGW')
    return result


def get_exports(**kwargs):
    """
    Returns the list of nfs-ganesha exports for each host that
    has the "ganesha" role.
    """
    return Ganesha.get_exports()


def save_exports(exports, **kwargs):
    """
    Saves the list of nfs-ganesha exports for each host that
    has the "ganesha" role.
    """
    if exports is None:
        return {'success': False, 'message': 'No exports config provided'}
    try:
        exports_json = json.loads(exports)
        return Ganesha.save_exports(exports_json)
    # pylint: disable=broad-except
    except Exception as exc:
        return {'success': False, 'message': str(exc)}


def deploy_exports(**kwargs):
    """
    Apply the changes to all gateways or a single minion
    """
    if 'minion' in kwargs:
        Ganesha.deploy_exports(kwargs['minion'])
    else:
        Ganesha.deploy_exports()


def status_exports(**kwargs):
    """
    Return status of exports
    """
    return Ganesha.check_exports_status()


def stop_exports(**kwargs):
    """
    Stop the Ganesha service
    """
    local = salt.client.LocalClient()
    if 'minion' in kwargs:
        return Ganesha.call_salt_module(local, kwargs['minion'], 'service.stop',
                                        ['nfs-ganesha'], minion=True)

    return Ganesha.call_salt_module(local, 'ganesha', 'service.stop', ['nfs-ganesha'], False)

__func_alias__ = {
                 'help_': 'help',
                 }
