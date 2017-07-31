# -*- coding: utf-8 -*-
import configobj
import os
import salt.utils

from salt.exceptions import CommandExecutionError


def _write_config_file(config_file, config):
    conf_content = ""
    write_log = set()
    with salt.utils.fopen(config_file, "r") as fir:
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
        with salt.utils.fopen(config_file, "w") as fiw:
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
    possible_paths = ("/etc/sysconfig/openattic", "/etc/openattic")
    for path in possible_paths:
        if os.access(path, os.F_OK) and os.access(path, os.R_OK | os.W_OK):
            return path
    raise CommandExecutionError(
        "No openATTIC config file found in the following locations: {}"
        .format(possible_paths))


def configure_salt_api(hostname, port, username, sharedsecret):
    config_file = _select_config_file_path()

    config = configobj.ConfigObj(config_file)
    if 'SALT_API_HOST' not in config:
        config['SALT_API_HOST'] = hostname
    if 'SALT_API_PORT' not in config:
        config['SALT_API_PORT'] = int(port)

    if 'SALT_API_EAUTH' not in config or config['SALT_API_EAUTH'] == 'auto':
        config['SALT_API_EAUTH'] = 'sharedsecret'

    config['SALT_API_USERNAME'] = username
    config['SALT_API_SHARED_SECRET'] = sharedsecret

    _write_config_file(config_file, config)


def configure_grafana(hostname):
    config_file = _select_config_file_path()

    config = configobj.ConfigObj(config_file)
    if 'GRAFANA_API_HOST' not in config:
        config['GRAFANA_API_HOST'] = hostname

    _write_config_file(config_file, config)

