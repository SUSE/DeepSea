# pylint: disable=no-member
# -*- coding: utf-8 -*-
"""
List the rbd images
"""

from __future__ import absolute_import
import sys
from subprocess import Popen, PIPE
import logging
log = logging.getLogger(__name__)
try:
    import rados
    import rbd
except ImportError:
    log.debug("Rados or RBD is not installed.")
    sys.exit(1)


# pylint: disable=too-few-public-methods
class ClusterUnhealthy(Exception):
    """
    If we query a cluster that has issues with data consistency/integrety we
    will end up with stuck/longrunning processes. Avoid that by raising early
    """


class Cluster(object):
    """
    Handling cluster operations within this class
    """

    def __init__(self):
        self.cluster = self._connect()

    # pylint: disable=no-self-use
    def _connect(self):
        """
        Establish a connection to the Ceph cluster
        """
        try:
            original = sys.stdout
            cluster = rados.Rados(conffile='/etc/ceph/ceph.conf')
            cluster.connect(timeout=25)
            sys.stdout = original
            return cluster
        except IOError as err:
            log.debug("Can't parse ceph.conf. {}".format(err.__str__()))
            return False

    # pylint: disable=no-self-use
    def _get_pg_state(self, state):
        """
        Check state of pg's to avoid hanging read requests against the cluster

        param: state
        type: string
        returns: bool
        """
        cmd = ['/usr/bin/ceph', 'pg', 'dump_stuck', state]
        rbd_proc = Popen(cmd, stdout=PIPE, stderr=PIPE)
        # ret is always 0, no need for the rc
        _, stderr = rbd_proc.communicate()
        if stderr != 'ok':
            return False

    def is_ok(self):
        """
        Checks pgs for all known and important states

        :returns: bool
        """
        for state in ['stale', 'inactive', 'unclean']:
            if not self._get_pg_state(state):
                return False
        return True


# pylint: disable=too-few-public-methods
class CephImages(object):
    """
    Class used to retrieve an list of rbd images from ceph
    """

    def __init__(self):
        self.images = {}
        self.cluster_o = Cluster()
        self.cluster = self.cluster_o.cluster

    def list(self):
        """
        Returns a dict of all rbd images in a pool

        :returns: dict
        """
        if not self.cluster_o.is_ok():
            raise ClusterUnhealthy("Cluster is unhealthy. Not querying for rbd images")
        try:
            for pool in self.cluster.list_pools():
                ioctx = self.cluster.open_ioctx(pool)
                try:
                    rbd_inst = rbd.RBD()
                    self.images[pool] = rbd_inst.list(ioctx)
                finally:
                    ioctx.close()
        finally:
            self.cluster.shutdown()
        return self.images


def list_():
    """
    Public function exposed for salt
    Invoked with: salt <target> cephimages.list
    The cli equivalent is: /usr/bin/rbd -p pool ls
    """
    CephImages().list()

__func_alias__ = {
                 'list_': 'list',
                 }
