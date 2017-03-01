#!/usr/bin/python

import logging
import sys
import os
import json
import salt.client

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
	self.data = {}

    def populate(self):
	"""
	Parse grains for all network interfaces on igw roles.  Possibly
	select public interface.
	Read a Salt mine of an unwritten module that lists all images
	and their pools.
	Read the existing lrbd.conf
	"""
	self.data['config'] = self.config()
	self.data['interfaces'] = self.interfaces()

	#self.data.append({ 'name': 'images', 'data': content })
	return self.data

    def interfaces(self, wrapped=True):
	"""
	"""
	_stdout = sys.stdout
	sys.stdout = open(os.devnull, 'w')

	local = salt.client.LocalClient()
	igws = local.cmd("I@roles:igw", 'grains.get', [ 'ipv4'], expr_form="compound")
	sys.stdout = _stdout
	if wrapped:
	    config = []
	    for igw in igws.keys():
		for addr in igws[igw]:
		    if addr == '127.0.0.1':
			continue
		    config.append({ 'node': igw, 'addr': addr })
	    return config
	else:
	    for igw in igws.keys():
		igws[igw].remove('127.0.0.1')

	    return igws

    def images(self):
	"""
	"""

	pass


    def config(self, filename="/srv/salt/ceph/igw/cache/lrbd.conf"):
	"""
	"""
	if os.path.exists(filename):
	    return json.loads(open(filename).read())

    def save(self, **kwargs):
	"""
	Convert data to lrbd sections if necessary.
	Ensure ceph.igw.config is disabled (or better create sls file
	that says configured by gui)
	Overwrite /srv/salt/ceph/igw/cache/lrbd.conf
	"""
	pass



def populate_iscsi(**kwargs):
    """
    Populate the iSCSI view
    """
    i = Iscsi(**kwargs)
    return i.populate()

def save_iscsi(**kwargs):
    """
    Save the iSCSI configuration
    """
    i = Iscsi()
    return i.save()

def iscsi_config(**kwargs):
    i = Iscsi(**kwargs)
    return i.config()

def iscsi_interfaces(**kwargs):
    i = Iscsi(**kwargs)
    return i.interfaces(wrapped=False)
