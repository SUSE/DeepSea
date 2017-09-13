# -*- coding: utf-8 -*-

import salt.config
import logging
from subprocess import call, Popen, PIPE
import os
import json
import boto
import boto.s3.connection
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


def create_bucket(**kwargs):
    s3conn = boto.connect_s3(
        aws_access_key_id=kwargs['access_key'],
        aws_secret_access_key=kwargs['secret_key'],
        host=kwargs['host'],
        is_secure=kwargs['ssl'],
        port=kwargs['port'],
        calling_format=boto.s3.connection.OrdinaryCallingFormat(),
    )
    try:
        s3conn.create_bucket(kwargs['bucket_name'])
    except boto.exception.S3CreateError:
        return False
    return True


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

