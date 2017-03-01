#!/usr/bin/python

import logging
import os
import json

log = logging.getLogger(__name__)


"""
Consolidate any user interface calls for Wolffish and openATTIC.

Guiding ideas:
- Provide all data necessary for one view in one call.  That is, minimize
  the number of ajax calls
- Accommodate the data structures of the web (i.e. list of dictionaries)
- Do not query Ceph directly.  Performance will vary too greatly.  Use other
  modules with Salt mines.
"""

class Iscsi(object):
    """
    Populating the view requires network interfaces by host, images by pool
    and the current lrbd configuration.
    Saving the choices requires writing out the lrbd.conf
    """


    def __init__(self, **kwargs):
	"""
	"""
	self.data = []

    def populate(**kwargs):
	"""
	Parse grains for all network interfaces on igw roles.  Possibly
	select public interface.
	Read a Salt mine of an unwritten module that lists all images
	and their pools.
	Read the existing lrbd.conf
	"""
	content = self._config()
	self.data.append({ 'name': 'config', 'data': content })

	#self.data.append({ 'name': 'interfaces', 'data': content })
	#self.data.append({ 'name': 'images', 'data': content })

    def _igw_interfaces():
	"""
	"""
	pass

    def _images():
	"""
	"""
	pass

    def _config(filename="/srv/salt/ceph/igw/cache/lrbd.conf"):
	"""
	"""
	if os.path.exists(filename):
	    return json.loads(open(filename).read())

    def save(**kwargs):
	"""
	Convert data to lrbd sections if necessary.
	Ensure ceph.igw.config is disabled (or better create sls file
	that says configured by gui)
	Overwrite /srv/salt/ceph/igw/cache/lrbd.conf
	"""
	pass


def populate_iscsi():
    """
    Populate the iSCSI view
    """
    i = Iscsi()
    return i.populate


def save_iscsi(**kwargs):
    """
    Save the iSCSI configuration
    """
    i = Iscsi()
    return i.save(**kwargs)
