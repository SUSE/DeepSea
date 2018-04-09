# -*- coding: utf-8 -*-
# pylint: disable=fixme

"""
RadosGW related functions for users, configurations, keys and buckets
"""

from __future__ import absolute_import
import logging
# pylint: disable=incompatible-py3-code
from subprocess import Popen, PIPE
import os
import json
import re
try:
    import salt.config
except ImportError:
    logging.error("Could not import salt.config")
# pylint: disable=import-error,3rd-party-module-not-gated
import boto
# pylint: disable=import-error,3rd-party-module-not-gated
import boto.s3.connection
# pylint: disable=import-error,3rd-party-module-not-gated
import boto.exception


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
    return


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
                    # pylint: disable=redefined-variable-type
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
        return

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


def endpoints(cluster='ceph'):
    """
    Returns an array of data structures for each gateway
    """
    result = []

    search = "I@cluster:{}".format(cluster)
    __opts__ = salt.config.client_config('/etc/salt/master')
    pillar_util = salt.utils.master.MasterPillarUtil(search, "compound",
                                                     use_cached_grains=True,
                                                     grains_fallback=False,
                                                     opts=__opts__)
    cached = pillar_util.get_minion_pillar()
    for minion in cached:
        if 'rgw_endpoint' in cached[minion]:
            match = re.search(r'http(s?)://(.+):?(\d*)', cached[minion]['rgw_endpoint'])
            if match:
                result.append({
                    'host': match.group(2),
                    'port': int(match.group(3)) if match.group(3) else 7480,
                    'ssl': match.group(1) == 's',
                    'url': cached[minion]['rgw_endpoint']
                })
            else:
                result.append({
                    'host': None,
                    'port': None,
                    'ssl': None,
                    'url': cached[minion]['rgw_endpoint']
                })
            return result

    port = '7480'  # civetweb default port
    ssl = ''
    admin_path = 'admin'
    rgw_names = ['rgw']
    for minion in cached:
        if 'rgw_configurations' in cached[minion]:
            # TODO: where is the master minion when we need it
            rgw_names = cached[minion]['rgw_configurations']

    conf_file_dir = "/srv/salt/ceph/configuration/files/"
    rgw_conf_files = {}
    for rgw_name in rgw_names:
        # Check for user created configurations
        pathname = "{}/ceph.conf.d/{}.conf".format(conf_file_dir, rgw_name)
        if os.path.exists(pathname):
            rgw_conf_files[pathname] = rgw_name
            continue

        pathname = "{}/{}.conf".format(conf_file_dir, rgw_name)
        if os.path.exists(pathname):
            rgw_conf_files[pathname] = rgw_name

    for pathname in rgw_conf_files:
        with open(pathname) as rgw_conf_file:
            for line in rgw_conf_file:
                if line:
                    match = re.search(r'rgw.*frontends.*=.*port=(\d+)(s?)', line)
                    if match:
                        # pylint: disable=redefined-variable-type
                        port = int(match.group(1))
                        ssl = match.group(2)

                    match = re.search(r'rgw.*admin.*entry.*=\s*(\w+)', line)
                    if match:
                        admin_path = match.group(1)

        local = salt.client.LocalClient()

        fqdns = local.cmd('I@roles:'+ rgw_conf_files[pathname], 'grains.item',
                          ['fqdn'], tgt_type="compound")
        for _, grains in fqdns.items():
            log.warning("fqdns: {}".format(fqdns))
            result.append({
                'host': grains['fqdn'],
                'port': port,
                'ssl': ssl == 's',
                'url': "http{}://{}:{}/{}".format(ssl, grains['fqdn'], port, admin_path)
            })
    return result


def s3connect(user):
    """
    Return an S3 connection
    """
    if access_key(user) is None or secret_key(user) is None:
        return
    endpoint = endpoints()[0]

    s3conn = boto.connect_s3(
        aws_access_key_id=access_key(user),
        aws_secret_access_key=secret_key(user),
        host=endpoint['host'],
        is_secure=bool(endpoint['ssl']),
        port=int(endpoint['port']),
        calling_format=boto.s3.connection.OrdinaryCallingFormat(),
    )
    return s3conn


def create_bucket(**kwargs):
    """
    Create a bucket for a user
    """
    s3conn = s3connect(kwargs['user'])
    if s3conn is None:
        return False
    try:
        s3conn.create_bucket(kwargs['bucket_name'])
    except boto.exception.S3CreateError:
        return False
    return True


def lookup_bucket(user, bucket):
    """
    Query a bucket for a user
    """
    s3conn = s3connect(user)
    if s3conn is None:
        return False
    if s3conn.lookup(bucket, validate=True) is None:
        return False

    return True
