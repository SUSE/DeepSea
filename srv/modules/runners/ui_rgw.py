# -*- coding: utf-8 -*-

"""
Consolidate any user interface rgw calls for Wolffish and openATTIC.

All operations will happen using the rest-api of RadosGW.  The one execption
is getting the credentials for an administrative user which is implemented
here.
"""
from __future__ import absolute_import
import logging
import os
import json
import re
import glob
import salt.client
import salt.utils.minions

log = logging.getLogger(__name__)


class Radosgw(object):
    """
    Return a structure containing S3 keys and urls
    """

    def __init__(self, canned=None, cluster='ceph', pathname='/srv/salt/ceph/rgw/cache'):
        """
        Initialize and call routines
        """
        if canned:
            self._canned(int(canned))
        else:
            self.cluster = cluster
            self.credentials = {'access_key': None,
                                'secret_key': None,
                                'user_id': None,
                                'urls': [],
                                'success': False}

            self.pathname = pathname
            self._admin()
            self._urls()

    def _canned(self, canned):
        """
        Return examples for debugging without a working Ceph cluster
        """
        if canned == 1:
            self.credentials = {'access_key': "ABCDEFGHIJKLMNOPQRST",
                                'secret_key': "0123456789012345678901234567890123456789",
                                'urls': ["http://rgw1"]}
        elif canned == 2:
            self.credentials = {'access_key': "ABCDEFGHIJKLMNOPQRST",
                                'secret_key': "0123456789012345678901234567890123456789",
                                'urls': ["http://red1",
                                         "http://red2",
                                         "http://blue1:8000",
                                         "http://blue2:8000"]}

    def _admin(self, filename="user.admin.json"):
        """
        Expect admin user file; otherwise, search for first system user.
        Update access_key, secret_key
        """
        filepath = "{}/{}".format(self.pathname, filename)
        if os.path.exists(filepath):
            user = json.loads(open(filepath).read())
        else:
            user = None
            for user_file in glob.glob("{}/user.*".format(self.pathname)):
                user = json.loads(open(user_file).read())
                if 'system' in user and user['system'] == "true":
                    break
                user = None
            if not user:
                # No system user
                log.error("No system user for radosgw found")
                return
        self.credentials['access_key'] = user['keys'][0]['access_key']
        self.credentials['secret_key'] = user['keys'][0]['secret_key']
        self.credentials['user_id'] = user['keys'][0]['user']
        self.credentials['success'] = True

    def _urls(self):
        """
        Check for user defined endpoint; otherwise, return list of gateways as
        urls.
        """
        for endpoint in Radosgw.endpoints(self.cluster):
            self.credentials['urls'].append(endpoint['url'])

    @staticmethod
    def endpoints(cluster='ceph'):
        result = []
        local = salt.client.LocalClient()
        for master_node in local.cmd('*', "pillar.get", ["master_minion"]):
            result = local.cmd(master_node, 'rgw.endpoints', ['cluster=ceph'])[master_node]
            break
        return result


def credentials(canned=None, **kwargs):
    """
    Return the administrative credentials for the RadosGW
    """
    radosgw = Radosgw(canned)
    return radosgw.credentials


def endpoints(**kwargs):
    return Radosgw.endpoints()

def token(**kwargs):
    local = salt.client.LocalClient()

    if "data" not in kwargs:
        log.error("No data dictionary in kwargs.")
        return None

    data = kwargs["data"]

    if "ttype" not in data or "access" not in data or "secret" not in data:
        log.error("Token type, access key and secret id needed to compute RGW token.")
        return None

    ttype = data["ttype"]
    access = data["access"]
    secret = data["secret"]

    token = local.cmd('I@roles:rgw', 'cmd.shell', [ 'radosgw-token --encode --ttype={} --access={} --secret={}'.format(ttype, access, secret) ], expr_form="compound")
    return token
