# -*- coding: utf-8 -*-

"""
OpenATTIC configuration operations
"""

from __future__ import absolute_import
import os
import logging
from shutil import copyfile
# pylint: disable=import-error,3rd-party-module-not-gated
import configobj

log = logging.getLogger(__name__)

try:
    import salt.utils
except ImportError:
    logging.error("Could not import salt.util")

try:
    from salt.exceptions import CommandExecutionError
except ImportError:
    logging.error("Could not import salt.util")


def _write_config_file(config_file, config):
    """
    Create the openATTIC configuration file
    """
    conf_content = ""
    write_log = set()
    with open(config_file, "r") as fir:
        for line in fir:
            sline = line.strip()
            idx = sline.find('=')
            if idx != -1 and not sline.startswith('#'):
                key = sline[:idx].strip()
                if key in config:
                    if isinstance(config[key], int):
                        val_str = "{}".format(config[key])
                    else:
                        val_str = '"{}"'.format(config[key])
                    conf_content += '{}={}\n'.format(key, val_str)
                    write_log.add(key)
                    continue

            conf_content += line

    for key, val in config.items():
        if key not in write_log:
            if isinstance(val, int):
                val_str = "{}".format(val)
            else:
                val_str = '"{}"'.format(val)
            conf_content += '{}={}\n'.format(key, val_str)

    try:
        with open(config_file, "w") as fiw:
            fiw.write(conf_content)
    except IOError as ex:
        if ex.errno == 13:
            raise CommandExecutionError("Permission denied while writting settings to {}.\n"
                                        "Please check file permissions for user \"openattic\""
                                        .format(config_file))
        else:
            raise CommandExecutionError("Error while writting settings to {}: IOError errno={}"
                                        .format(config_file, ex.errno))


def _select_config_file_path():
    """
    Return an openATTIC configuration pathname
    """
    possible_paths = ("/etc/default/openattic", "/etc/sysconfig/openattic")
    for path in possible_paths:
        if os.access(path, os.F_OK) and os.access(path, os.R_OK | os.W_OK):
            return path
    raise CommandExecutionError(
        ("No openATTIC config file found in the following locations: "
         "{}".format(possible_paths)))


def configure_salt_api(hostname, port, username, sharedsecret):
    """
    Update the SALT API configuration
    """
    config_file = _select_config_file_path()

    config = configobj.ConfigObj(config_file)

    config['SALT_API_HOST'] = hostname
    config['SALT_API_PORT'] = int(port)
    config['SALT_API_EAUTH'] = 'sharedsecret'
    config['SALT_API_USERNAME'] = username
    config['SALT_API_SHARED_SECRET'] = sharedsecret

    # Write backup file
    copyfile(config_file, "{}.deepsea.bak".format(config_file))
    _write_config_file(config_file, config)


def configure_grafana(hostname):
    """
    Update the Grafana configuration
    """
    config_file = _select_config_file_path()

    config = configobj.ConfigObj(config_file)

    config['GRAFANA_API_HOST'] = hostname

    # Write backup file
    copyfile(config_file, "{}.deepsea.bak".format(config_file))
    _write_config_file(config_file, config)
