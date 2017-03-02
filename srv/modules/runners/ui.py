#!/usr/bin/python

import logging
import sys
import os
import json
import yaml
import salt.client
import salt.utils.minions

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
	self.friendly_dumper = yaml.SafeDumper
	self.friendly_dumper.ignore_aliases = lambda self, data: True
	self.local = salt.client.LocalClient()

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
	self.data['images'] = self.images()

	return self.data

    def interfaces(self, wrapped=True):
	"""
	"""
	_stdout = sys.stdout
	sys.stdout = open(os.devnull, 'w')

	igws = self.local.cmd("I@roles:igw", 'grains.get', [ 'ipv4'], expr_form="compound")
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

    def images(self, wrapped=True):
	"""
	"""
	__opts__ = salt.config.client_config('/etc/salt/master')
	result = salt.utils.minions.mine_get('I@roles:master', 'cephimages.list', 'compound', __opts__)
	if wrapped:
	    config = []
	    for master in result.keys():
		for pool in result[master]:
		    config.append({ 'pool': pool, 'img': result[master][pool] })
		break
	    return config
	else:
	    for master in result.keys():
		return result[master]


    def config(self, filename="/srv/salt/ceph/igw/cache/lrbd.conf"):
	"""
	"""
	if os.path.exists(filename):
	    return json.loads(open(filename).read())

    def save(self, filename="/srv/salt/ceph/igw/cache/lrbd.conf", **kwargs):
	"""
	Convert data to lrbd sections if necessary.
	Ensure ceph.igw.config is disabled (or better create sls file
	that says configured by gui)
	Overwrite /srv/salt/ceph/igw/cache/lrbd.conf
	"""
	if 'data' in kwargs:
	    self._set_igw_config(**kwargs)
	    contents = kwargs['data']
	    with open(filename, 'w') as conf:
		conf.write(json.dumps(contents, indent=4) + '\n')
	else:
	    log.error("No JSON data passed")

    def _set_igw_config(self, cluster='ceph', **kwargs):
	"""
	Add igw_config to cluster.yml

	Comments are removed from cluster.yml
	"""
	if 'filename' in kwargs:
	    filename = kwargs['filename']
	else:
	    filename = '/srv/pillar/ceph/stack/{}/cluster.yml'.format(cluster)
	contents = {}
	with open(filename, 'r') as yml:
	    contents = yaml.safe_load(yml)
	contents['igw_config'] = 'default-ui'
	with open(filename, 'w') as yml:
	    yml.write(yaml.dump(contents, Dumper=self.friendly_dumper,
						  default_flow_style=False))
	# refresh pillar
	self.local.cmd("I@roles:master", 'saltutils.pillar_refresh', [ ''], expr_form="compound")


    def canned_populate(self, canned):
	"""
	Return all canned data

	Note: could add samples from lrbd for config
	"""
	self.data['config'] = ''
	self.data['interfaces'] = self.canned_interfaces(canned)
	self.data['images'] = self.canned_images(canned)

	return self.data

    def canned_images(self, canned, wrapped=True):
	"""
	Return canned example for pools and images
	"""
	images = { 1: { 'rbd' : [ 'demo1', 'demo2', 'demo3' ] },
		   2: { 'car' : [ 'cement' ],
			'whirl' : [ 'cheese' ],
			'rbd': [ 'wood', 'writers', 'city' ],
			'swimming': [ 'cell' ] } }
	if wrapped:
	    config = []
	    for pool in images[canned].keys():
		for img in images[canned][pool]:
		    config.append({ 'pool': pool, 'img': img })
	    return config
	else:
	    return images[canned]

    def canned_interfaces(self, canned, wrapped=True):
	"""
	Return canned example for nodes and addresses
	"""
	interfaces = { 1: { 'igw1' : [ '192.168.0.2', '192.168.1.2', '192.168.2.2' ] },
		       2: { 'node1': [ '10.0.0.10' ],
			    'node2': [ '10.0.0.11' ],
			    'node3': [ '10.0.0.12',
				       '172.16.31.12',
				       '192.168.10.112' ],
			    'node4': [ '1.2.3.4' ] } }
	if wrapped:
	    config = []
	    for node in interfaces[canned].keys():
		for addr in interfaces[canned][node]:
		    config.append({ 'node': node, 'addr': addr })
	    return config
	else:
	    return interfaces[canned]

def populate_iscsi(**kwargs):
    """
    Populate the iSCSI view
    """
    i = Iscsi(**kwargs)
    if 'canned' in kwargs:
	return i.canned_populate(kwargs['canned'])
    return i.populate()

def save_iscsi(**kwargs):
    """
    Save the iSCSI configuration
    """
    i = Iscsi()
    return i.save(**kwargs)

def iscsi_config(**kwargs):
    i = Iscsi(**kwargs)
    return i.config()

def iscsi_interfaces(**kwargs):
    i = Iscsi(**kwargs)
    if 'canned' in kwargs:
	return i.canned_interfaces(kwargs['canned'], wrapped=False)
    return i.interfaces(wrapped=False)

def iscsi_images(**kwargs):
    i = Iscsi(**kwargs)
    if 'canned' in kwargs:
	return i.canned_images(kwargs['canned'], wrapped=False)
    return i.images(wrapped=False)
