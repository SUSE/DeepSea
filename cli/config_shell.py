# -*- coding: utf-8 -*-
"""
DeepSea configuration shell
"""

from __future__ import absolute_import
from __future__ import print_function

import logging
import os
import yaml
from collections import OrderedDict

from pyparsing import (alphanums, Empty, Group, OneOrMore, Optional,
                       ParseResults, Regex, Suppress, Word)

import configshell_fb as configshell
from configshell_fb.shell import locatedExpr

from .common import PrettyPrinter as PP, check_terminal_utf8_support
from .salt_client import SaltClient


# pylint: disable=C0103
logger = logging.getLogger(__name__)


class OptionHandler(object):
    def value(self):
        raise NotImplementedError()

    def save(self):
        raise NotImplementedError()

    def reset(self):
        raise NotImplementedError()

    def read_only(self):
        raise NotImplementedError()


class PillarHandler(OptionHandler):
    def __init__(self, pillar_path):
        self.pillar_path = pillar_path

    def value(self):
        return PillarManager.get(self.pillar_path), \
               None if PillarManager.is_original(self.pillar_path) else True

    def save(self, value):
        PillarManager.set(self.pillar_path, value)

    def reset(self):
        PillarManager.reset(self.pillar_path)

    def read_only(self):
        return False


class DashboardCredsHandler(PillarHandler):
    def __init__(self, pillar_path, grains_path):
        super(DashboardCredsHandler, self).__init__(pillar_path)
        self.grains_path = grains_path

    def _get_user_password(self):
        result = SaltClient.caller().cmd('grains.get', self.grains_path)
        if result and len(result) == 1:
            return next(iter(result.items()))
        return None

    def read_only(self):
        result = SaltClient.caller().cmd('grains.get', self.grains_path)
        return result and len(result) == 1


class DashboardPasswordHandler(DashboardCredsHandler):
    def __init__(self, pillar_path, grains_path):
        super(DashboardPasswordHandler, self).__init__(pillar_path, grains_path)

    def value(self):
        uspw = self._get_user_password()
        if uspw:
            return uspw[1], not self.read_only()
        return super(DashboardCredsHandler, self).value()


class DashboardUsernameHandler(DashboardCredsHandler):
    def __init__(self, pillar_path, grains_path):
        super(DashboardUsernameHandler, self).__init__(pillar_path, grains_path)

    def value(self):
        uspw = self._get_user_password()
        if uspw:
            return uspw[0], not self.read_only()
        return super(DashboardUsernameHandler, self).value()


class DeepSeaMinionsHandler(PillarHandler):
    def __init__(self, pillar_path):
        super(DeepSeaMinionsHandler, self).__init__(pillar_path)

    def value(self):
        PillarManager.load('deepsea_minions.sls')
        val = PillarManager.get(self.pillar_path)
        return val, True if val != 'G@deepsea:*' else None

    def save(self, value):
        PillarManager.load('deepsea_minions.sls')
        PillarManager.set(self.pillar_path, value, 'deepsea_minions.sls')

    def reset(self):
        PillarManager.load('deepsea_minions.sls')
        PillarManager.set(self.pillar_path, 'G@deepsea:*', 'deepsea_minions.sls')


DEEPSEA_OPTIONS = {
    'Ceph_Dashboard': {
        'help': '''
                Ceph Dashboard Configuration
                ============================
                Options for configuring the Ceph Dashboard manager module.
                ''',
        'options': {
            'username': {
                'default': 'admin',
                'help': "The administrator account username",
                'handler': DashboardUsernameHandler('dashboard_user', 'dashboard_creds')
            },
            'password': {
                'default': None,
                'default_text': 'randomly generated',
                'help': "The administrator account password",
                'handler': DashboardPasswordHandler('dashboard_password', 'dashboard_creds')
            },
            'port': {
                'default': 8080,
                'help': "The TCP port where the dashboard will be listening",
                'handler': PillarHandler('dashboard_port')
            },
            'ssl': {
                'type': 'flag',
                'default': True,
                'help': "Enables/disables HTTPS access to Ceph Dashboard",
                'handler': PillarHandler('dashboard_ssl'),
                'options': {
                    'cert_file': {
                        'default': None,
                        'default_text': "self-signed certificate",
                        'help': 'Path to SSL certificate',
                        'handler': PillarHandler('dashboard_ssl_cert'),
                    },
                    'cert_key_file': {
                        'default': None,
                        'default_text': "self-signed certificate",
                        'help': 'Path SSL certificate private key',
                        'handler': PillarHandler('dashboard_ssl_key'),
                    },
                    'port': {
                        'default': 8443,
                        'help': "The TCP port where the dashboard will be listening for HTTPS",
                        'handler': PillarHandler('dashboard_ssl_port')
                    },
                }
            },
        }
    },
    'iSCSI_Gateway': {
        'help': '''
                iSCSI Gateway Configuration
                ===========================
                Options for configuring the iSCSI Gateways configuration.
                Each iSCSI gateway uses ceph-iscsi to manage the LIO configuration.
                ''',
        'options': {
            'username': {
                'default': 'admin',
                'help': 'REST API access username',
                'handler': PillarHandler('ceph_iscsi_username')
            },
            'password': {
                'default': 'admin',
                'help': 'REST API access password',
                'handler': PillarHandler('ceph_iscsi_password')
            },
            'port': {
                'default': 5000,
                'help': 'REST API port',
                'handler': PillarHandler('ceph_iscsi_port')
            },
            'ssl': {
                'type': 'flag',
                'default': False,
                'help': "Enables/disables HTTPS access to ceph-iscsi REST API",
                'handler': PillarHandler('ceph_iscsi_ssl'),
                'options': {
                    'cert_file': {
                        'default': None,
                        'default_text': "self-signed certificate",
                        'help': 'Path to SSL certificate',
                        'handler': PillarHandler('ceph_iscsi_ssl_cert'),
                    },
                    'cert_key_file': {
                        'default': None,
                        'default_text': "self-signed certificate",
                        'help': 'Path SSL certificate private key',
                        'handler': PillarHandler('ceph_iscsi_ssl_key'),
                    }
                }
            },
        }
    },
    'Global_Options': {
        'help': '''
                DeepSea Global Options Configuration
                ====================================
                Options that affect DeepSea's execution.
                ''',
        'options': {
            'DEV_ENV': {
                'type': 'flag',
                'default': False,
                'help': 'Enables/disables DeepSea development environment mode.'
                        'When enabled allows to deploy a cluster in less than four nodes.',
                'handler': PillarHandler('DEV_ENV')
            },
            'deepsea_minions': {
                'handler': DeepSeaMinionsHandler('deepsea_minions'),
                'help': """
                        Sets the targeting of Salt minions used by DeepSea.
                        By default DeepSea targets by grain using 'G@deepsea'
                        """
            }
        }
    },
    'Updates': {
        'help': '''
                Updates Configuration
                ====================================
                Options that affect ceph.updates state execution.
                ''',
        'options': {
            'package': {
                'type': 'flag',
                'default': True,
                'help': 'Enables/disables regular packages updates',
                'handler': PillarHandler('package_updates'),
            },
            'auto_reboot': {
                'type': 'flag',
                'default': True,
                'help': 'Enables/disables automatic reboot after package updates.',
                'handler': PillarHandler('auto_reboot')
            },
            'kernel': {
                'type': 'flag',
                'default': True,
                'help': 'Enables/disables automatic kernel updates.',
                'handler': PillarHandler('kernel_update')
            }
        }
    },
    # 'States_Override': {
    #     'help': '''
    #             DeepSea stages's states overrides
    #             =================================
    #             Here you can override the sls file that should be used as the state
    #             implementation.
    #             ''',
    #     'options': {
    #         'admin_init': {
    #             'default': 'default'
    #         }
    #     }
    # },
    'Time_Server': {
        'help': '''
                Time Server Deployment Options
                ==============================
                Options to customize time server deployment and configuration.
                ''',
        'options': {
            'server_hostname': {
                'default': None,
                'default_text': "salt master",
                'help': 'FQDN of the time server node',
                'handler': PillarHandler('time_server')
            }
        }
    }
}


class PillarManager(object):

    pillar_data = {}
    custom_data = {}

    @classmethod
    def load(cls, custom_file="stack/global.yml", reload=False):
        if not cls.pillar_data or reload:
            cls.pillar_data = SaltClient.caller().cmd('pillar.items')
        if custom_file not in cls.custom_data:
            cls.custom_data[custom_file] = cls._load_yaml(custom_file)

    @classmethod
    def get(cls, key):
        return cls._get_dict_value(cls.pillar_data, key)

    @classmethod
    def is_original(cls, key, custom_file="stack/global.yml"):
        return cls._get_dict_value(cls.custom_data[custom_file], key) is None

    @staticmethod
    def _get_dict_value(dict_, key_path):
        path = key_path.split(":")
        d = dict_
        while True:
            if len(path) == 1:
                if path[0] in d:
                    return d[path[0]]
                return None
            if path[0] in d:
                d = d[path[0]]
                path = path[1:]
            else:
                return None

    @staticmethod
    def _set_dict_value(dict_, key_path, value):
        path = key_path.split(":")
        d = dict_
        while True:
            if len(path) == 1:
                d[path[0]] = value
                return
            if path[0] not in d:
                d[path[0]] = {}
            d = d[path[0]]
            path = path[1:]

    @classmethod
    def _del_dict_key(cls, dict_, key_path):
        if not key_path:
            return
        path = key_path.split(":")
        d = dict_
        for p in path[:-1]:
            d = d[p]
        if isinstance(d[path[-1]], dict):
            if d[path[-1]]:
                return
        del dict_[path[-1]]
        cls._del_dict_key(dict_, ":".join(path[:-1]))

    @staticmethod
    def _load_yaml(custom_file):
        pillar_base_path = SaltClient.pillar_fs_path()
        full_path = "{}/ceph/{}".format(pillar_base_path, custom_file)
        if not os.path.exists(full_path):
            return {}
        with open(full_path, 'r') as f:
            data = yaml.load(f)
            if data is None:
                data = {}
        return data

    @staticmethod
    def _save_yaml(data, custom_file):
        pillar_base_path = SaltClient.pillar_fs_path()
        full_path = "{}/ceph/{}".format(pillar_base_path, custom_file)
        with open(full_path, 'w') as f:
            content = yaml.dump(data, default_flow_style=False)
            if content == '{}\n':
                f.write("")
            else:
                f.write(content)
            f.write("\n")

    @classmethod
    def set(cls, key, value, custom_file="stack/global.yml"):
        cls._set_dict_value(cls.custom_data[custom_file], key, value)
        cls._save_yaml(cls.custom_data[custom_file], custom_file)
        SaltClient.local().cmd('*', 'saltutil.pillar_refresh', tgt_type="compound")
        cls.load(custom_file, True)

    @classmethod
    def reset(cls, key, custom_file="stack/global.yml"):
        if cls._get_dict_value(cls.custom_data[custom_file], key) is None:
            return
        cls._del_dict_key(cls.custom_data[custom_file], key)
        cls._save_yaml(cls.custom_data[custom_file], custom_file)
        SaltClient.local().cmd('*', 'saltutil.pillar_refresh', tgt_type="compound")
        cls.load(custom_file, True)


class DeepSeaRoot(configshell.ConfigNode):
    help_intro = '''
                 DeepSea Configuration
                 =====================
                 This is a shell where you can manipulate DeepSea's configuration.
                 Each configuration option is present under a configuration group.

                 You can navigate through the groups and options using the B{ls} and
                 B{cd} commands as in a typical shell.

                 In each path you can type B{help} to see the available commands.
                 Different options might have different commands available.
                 '''

    def __init__(self, shell):
        configshell.ConfigNode.__init__(self, '/', shell=shell)

    def list_commands(self):
        return tuple(['cd', 'ls', 'help', 'exit'])

    def summary(self):
        return "", None


class GroupNode(configshell.ConfigNode):
    def __init__(self, group_name, help, parent):
        configshell.ConfigNode.__init__(self, group_name, parent)
        self.group_name = group_name
        self.help_intro = help

    def list_commands(self):
        return tuple(['cd', 'ls', 'help', 'exit', 'reset', 'set'])

    def summary(self):
        return "", None

    def ui_command_set(self, option_name, value):
        '''
        Sets the value of option
        '''
        self.get_child(option_name).ui_command_set(value)


    def ui_command_reset(self, option_name):
        '''
        Resets option value to the default
        '''
        self.get_child(option_name).ui_command_reset()


class OptionNode(configshell.ConfigNode):
    def __init__(self, option_name, option_dict, parent):
        configshell.ConfigNode.__init__(self, option_name, parent)
        self.option_name = option_name
        self.option_dict = option_dict
        self.help_intro = option_dict.get('help', '')
        self.value = None

    def list_commands(self):
        cmds = ['cd', 'ls', 'help', 'exit', 'reset']
        cmds.extend(self._list_commands())
        return tuple(cmds)

    def _find_value(self):
        if self.value is None:
            value = None
            if 'handler' in self.option_dict:
                value, val_type = self.option_dict['handler'].value()
            if value is not None:
                return value, val_type
            if 'default_text' in self.option_dict:
                return self.option_dict['default_text'], None
            if 'default' in self.option_dict:
                return self.option_dict['default'], None
            raise Exception("No default value found for {}".format(self.option_name))
        return self.value, True

    def summary(self):
        value, val_type = self._find_value()
        if isinstance(value, bool):
            value = 'enabled' if value else 'disabled'
        value_str = str(value)
        if val_type == False:
            value_str = "{} (RO)".format(value_str)
            val_type = None
        return value_str, val_type

    def ui_command_reset(self):
        '''
        Resets option value to the default
        '''
        if 'handler' in self.option_dict:
            self.option_dict['handler'].reset()
        else:
            self.value = None

    def _read_only(self):
        if 'handler' in self.option_dict:
            return self.option_dict['handler'].read_only()
        return False


class ValueOptionNode(OptionNode):
    def __init__(self, option_name, option_dict, parent):
        super(ValueOptionNode, self).__init__(option_name, option_dict, parent)

    def _list_commands(self):
        return ['set']

    def ui_command_set(self, value):
        '''
        Sets the value of option
        '''
        if self._read_only():
            raise Exception("Option {} cannot be modified".format(self.option_name))
        if 'handler' in self.option_dict:
            self.option_dict['handler'].save(value)
        else:
            self.value = value


class FlagOptionNode(OptionNode):
    def __init__(self, option_name, option_dict, parent):
        super(FlagOptionNode, self).__init__(option_name, option_dict, parent)

    def _list_commands(self):
        return ['enable', 'disable']

    def _set_option_value(self, bool_value):
        if self._read_only():
            raise Exception("Option {} cannot be modified".format(self.option_name))
        if 'handler' in self.option_dict:
            self.option_dict['handler'].save(bool_value)
        else:
            self.value = bool_value

    def ui_command_enable(self):
        '''
        Enables the option
        '''
        self._set_option_value(True)

    def ui_command_disable(self):
        '''
        Disables the option
        '''
        self._set_option_value(False)


def generate_config_shell_tree(shell):
    root_node = DeepSeaRoot(shell)
    for group_name, group_dict in DEEPSEA_OPTIONS.items():
        group_node = GroupNode(group_name, group_dict.get('help', ""), root_node)
        for option_name, option_dict in group_dict['options'].items():
            if option_dict.get('type', None) == 'flag':
                option_node = FlagOptionNode(option_name, option_dict, group_node)
            else:
                option_node = ValueOptionNode(option_name, option_dict, group_node)
            if 'options' in option_dict:
                for option_name, option_dict in option_dict['options'].items():
                    if option_dict.get('type', None) == 'flag':
                        FlagOptionNode(option_name, option_dict, option_node)
                    else:
                        ValueOptionNode(option_name, option_dict, option_node)


class DeepSeaConfigShell(configshell.ConfigShell):
    def __init__(self):
        super(DeepSeaConfigShell, self).__init__('~/.deepsea_config_shell')
        # Grammar of the command line
        command = locatedExpr(Word(alphanums + '_'))('command')
        var = Word(alphanums + ';,=_\+/.<>()~@:-%[]*')  # adding '*'
        value = var
        keyword = Word(alphanums + '_\-')
        kparam = locatedExpr(keyword + Suppress('=') + Optional(value, default=''))('kparams*')
        pparam = locatedExpr(var)('pparams*')
        parameter = kparam | pparam
        parameters = OneOrMore(parameter)
        bookmark = Regex('@([A-Za-z0-9:_.]|-)+')
        pathstd = Regex('([A-Za-z0-9:_.\[\]]|-)*' + '/' + '([A-Za-z0-9:_.\[\]/]|-)*') \
                | '..' | '.'
        path = locatedExpr(bookmark | pathstd | '*')('path')
        parser = Optional(path) + Optional(command) + Optional(parameters)
        self._parser = parser


def run_config_shell():
    has_utf8 = check_terminal_utf8_support()
    PP.p_bold("Loading DeepSea configuration ")
    PP.println(PP.orange(u"\u23F3") if has_utf8 else PP.orange("Running"))
    PillarManager.load()
    PP.print("\x1B[A\x1B[K")
    PP.p_bold("Loading DeepSea configuration ")
    PP.println(PP.green(PP.bold(u"\u2713")) if has_utf8 else PP.green("OK"))

    import re
    pattern = re.compile(r'B\{(\w+)\}')

    for line in DeepSeaRoot.help_intro.split('\n'):
        PP.println(re.sub(pattern, PP.bold(PP.dark_green(r'\1')), line.strip()))
    shell = DeepSeaConfigShell()
    generate_config_shell_tree(shell)
    while True:
        try:
            shell.run_interactive()
            break
        except Exception as ex:
            logger.exception(ex)
            print("An error occurred: {}".format(ex))


def run_config_cmdline(cmdline):
    PillarManager.load()
    shell = DeepSeaConfigShell()
    generate_config_shell_tree(shell)
    try:
        shell.run_cmdline(cmdline)
        print(PP.dark_green("OK"))
    except Exception as ex:
        logger.exception(ex)
        print("An error occurred: {}".format(ex))
