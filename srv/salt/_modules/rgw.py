# -*- coding: utf-8 -*-

import salt.config
import logging
from subprocess import call, Popen, PIPE
import os
import json
import boto
import boto.s3.connection
import boto.exception
import glob
import re

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
            return [ 'rgw' ]
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
            for rgw_config in  __pillar__['rgw_configurations']:
                if rgw_config in role:
                    return rgw_config
    return



def users(realm='default'):
    """
    Return the list of users for a realm.
    """
    cmd = "radosgw-admin user list --rgw-realm={}".format(realm)
    log.info("cmd: {}".format(cmd))
    proc = Popen(cmd.split(), stdout=PIPE, stderr=PIPE)
    proc.wait()
    log.debug("rc: {}".format(proc.returncode))
    if proc.returncode != '0':
        return json.loads(proc.stdout.read())
    return []

def add_users(pathname="/srv/salt/ceph/rgw/cache", jinja="/srv/salt/ceph/rgw/files/users.j2"):
    """
    Write each user to its own file.
    """
    users = __salt__['slsutil.renderer'](jinja)
    log.debug("users rendered: {}".format(users))

    if users is None or 'realm' not in users:
        return

    for realm in users['realm']:
        for user in users['realm'][realm]:
            if 'uid' not in user or 'name' not in user:
                raise ValueError('ERROR: please specify both uid and name')

            base_cmd = "radosgw-admin user create --uid={uid} --display-name={name}".format(
                uid=user['uid'],
                name=user['name'],
            )

            args = ''
            if 'email' in user:
                args += " --email=%s" % user['email']

            if 'system' in user and user['system'] is True:
                args += " --system"

            if 'access_key' in user:
                args += " --access-key=%s" % user['access_key']

            if 'secret' in user:
                args += " --secret=%s" % user['secret']

            command = base_cmd + args

            proc = Popen(command.split(), stdout=PIPE, stderr=PIPE)
            filename = "{}/user.{}.json".format(pathname, user['uid'])
            with open(filename, "w") as json:
                for line in proc.stdout:
                    json.write(line)
            for line in proc.stderr:
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
    if not user:
        raise ValueError("ERROR: no user specified")
    return _key(user, 'access_key', pathname)

def secret_key(user, pathname="/srv/salt/ceph/rgw/cache"):
    return _key(user, 'secret_key', pathname)

def endpoints(cluster='ceph'):
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
    rgw_conf_files = []
    for rgw_name in rgw_names:
        # Check for user created configurations
        pathname = "{}/ceph.conf.d/{}.conf".format(conf_file_dir, rgw_name)
        if os.path.exists(pathname):
            rgw_conf_files.append(pathname)
            continue

        pathname = "{}/{}.conf".format(conf_file_dir, rgw_name)
        if os.path.exists(pathname):
            rgw_conf_files.append(pathname)

    for pathname in rgw_conf_files:
        with open(pathname) as rgw_conf_file:
            for line in rgw_conf_file:
                if line:
                    match = re.search(r'rgw.*frontends.*=.*port=(\d+)(s?)', line)
                    if match:
                        port = int(match.group(1))
                        ssl = match.group(2)

                    match = re.search(r'rgw.*admin.*entry.*=\s*(\w+)', line)
                    if match:
                        admin_path = match.group(1)

        local = salt.client.LocalClient()
        fqdns = local.cmd('I@roles:'+ rgw_name, 'grains.item', ['fqdn'], expr_form="compound")
        for _, grains in fqdns.items():
            result.append({
                'host': grains['fqdn'],
                'port': port,
                'ssl': ssl == 's',
                'url': "http{}://{}:{}/{}".format(ssl, grains['fqdn'], port, admin_path)
            })
    return result


def s3connect(user):
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
    s3conn = s3connect(kwargs['user'])
    try:
        s3conn.create_bucket(kwargs['bucket_name'])
    except boto.exception.S3CreateError:
        return False
    return True

def lookup_bucket(user, bucket):
    s3conn = s3connect(user)
    if s3conn.lookup(bucket, validate=True) is None:
        return False

    return True
