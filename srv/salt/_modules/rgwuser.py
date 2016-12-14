#!/usr/bin/python

import os
import json


def _key(user, field, pathname):
    """
    Read the filename and return the key value.  If it does not exist,
    generate one.
    """
    filename = "{}/user.{}.json".format(pathname, user)
    if os.path.exists(filename):
        with open(filename, 'r') as user_file:
            data = json.load(user_file)

    return data['keys'][0][field]

def access_key(user, pathname="/srv/salt/ceph/rgw/cache"):
    return _key(user, 'access_key', pathname)

def secret_key(user, pathname="/srv/salt/ceph/rgw/cache"):
    return _key(user, 'secret_key', pathname)

#print access_key('demo', pathname="/local/eric/src/DeepSea/srv/salt/ceph/rgw/cache")
#print secret_key('demo', pathname="/local/eric/src/DeepSea/srv/salt/ceph/rgw/cache")
