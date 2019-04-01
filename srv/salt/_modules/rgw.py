# -*- coding: utf-8 -*-
# pylint: disable=fixme

"""
RadosGW related functions for users, configurations and keys
"""

from __future__ import absolute_import
import logging
# pylint: disable=incompatible-py3-code
from subprocess import Popen, PIPE
import os
import json

log = logging.getLogger(__name__)


def configurations():
    """
    Return the rgw configurations.  The three answers are

    rgw_configurations as defined in the pillar
    rgw if defined
    [] for no rgw
    """
    if 'roles' in __pillar__:
        if 'rgw_configurations' in __pillar__:
            log.info("rgw_c: {}".format(__pillar__['rgw_configurations']))
            return list(set(__pillar__['rgw_configurations']) &
                        set(__pillar__['roles']))

        if 'rgw' in __pillar__['roles']:
            return ['rgw']
    return []


def configuration(role):
    """
    Return the equivalent rgw role for the ganesha role. For instance,
    the ganesha roles silver and silver-common will both return silver.
    """
    if role == 'ganesha':
        return 'rgw'
    if 'roles' in __pillar__:
        if 'rgw_configurations' in __pillar__:
            for rgw_config in __pillar__['rgw_configurations']:
                if rgw_config in role:
                    return rgw_config
    return None


def users(realm='default', contains=None):
    """
    Return the list of users for a realm.
    """
    cmd = "radosgw-admin user list --rgw-realm={}".format(realm)
    retcode, stdout, _ = __salt__['helper.run'](cmd)
    if retcode != '0':
        if contains:
            return [item for item in json.loads(stdout) if contains in item]
        return json.loads(stdout)
    return []


def add_users(pathname="/srv/salt/ceph/rgw/cache", jinja="/srv/salt/ceph/rgw/files/users.j2"):
    """
    Write each user to its own file.
    """
    conf_users = __salt__['slsutil.renderer'](jinja)
    log.debug("users rendered: {}".format(conf_users))

    if conf_users is None or 'realm' not in conf_users:
        return

    for realm in conf_users['realm']:
        # Get the existing users.
        existing_users = users(realm)

        for user in conf_users['realm'][realm]:
            if 'uid' not in user or 'name' not in user:
                raise ValueError('ERROR: please specify both uid and name')

            filename = "{}/user.{}.json".format(pathname, user['uid'])

            # Create the RGW user if it does not exist.
            if not user['uid'] in existing_users:
                base_cmd = ("radosgw-admin user create --uid={uid} "
                            "--display-name={name} "
                            "--rgw-realm={realm}".format(uid=user['uid'],
                                                         name=user['name'],
                                                         realm=realm))
                args = ''
                if 'email' in user:
                    args += " --email={}".format(user['email'])
                if 'system' in user and user['system']:
                    args += " --system"
                if 'access_key' in user:
                    args += " --access-key={}".format(user['access_key'])

                if 'secret' in user:
                    args += " --secret={}".format(user['secret'])
                command = base_cmd + args
                proc = Popen(command.split(), stdout=PIPE, stderr=PIPE)
                filename = "{}/user.{}.json".format(pathname, user['uid'])
                with open(filename, "w") as _json:
                    for line in proc.stdout:
                        line = __salt__['helper.convert_out'](line)
                        _json.write(line)
                for line in proc.stderr:
                    line = __salt__['helper.convert_out'](line)
                    log.info("stderr: {}".format(line))
                    proc = Popen(command.split(), stdout=PIPE, stderr=PIPE)
                    with open(filename, "w") as _json:
                        # pylint: disable=redefined-outer-name
                        for line in proc.stdout:
                            line = __salt__['helper.convert_out'](line)
                            _json.write(line)
                    # pylint: disable=redefined-outer-name
                    for line in proc.stderr:
                        line = __salt__['helper.convert_out'](line)
                        log.info("stderr: {}".format(line))

                proc.wait()
            else:
                # Create the JSON file if it does not exist. This happens
                # when the RGW user was manually created beforehand.
                # pylint: disable=useless-else-on-loop
                if not os.path.exists(filename):
                    args = ['radosgw-admin', 'user', 'info']
                    args.extend(['--uid', user['uid']])
                    args.extend(['--rgw-realm', realm])
                    proc = Popen(args, stdout=PIPE, stderr=PIPE)
                    with open(filename, "w") as _json:
                        for line in proc.stdout:
                            line = __salt__['helper.convert_out'](line)
                            _json.write(line)
                    for line in proc.stderr:
                        line = __salt__['helper.convert_out'](line)
                        log.info("stderr: {}".format(line))
                    proc.wait()


def _key(user, field, pathname):
    """
    Read the filename and return the key value.
    """
    data = None
    filename = "{}/user.{}.json".format(pathname, user)
    log.info("filename: {}".format(filename))
    if os.path.exists(filename):
        with open(filename, 'r') as user_file:
            data = json.load(user_file)
    else:
        return None

    return data['keys'][0][field]


def access_key(user, pathname="/srv/salt/ceph/rgw/cache"):
    """
    Returns the access key for a given user
    """
    if not user:
        raise ValueError("ERROR: no user specified")
    return _key(user, 'access_key', pathname)


def secret_key(user, pathname="/srv/salt/ceph/rgw/cache"):
    """
    Returns the secret key for a given user
    """
    return _key(user, 'secret_key', pathname)
