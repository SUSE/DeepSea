#!/usr/bin/python

"""
Consolidate any user interface iscsi calls for Wolffish and openATTIC.

Guiding ideas:
- Provide all data necessary for one view in one call.  That is, minimize
  the number of ajax calls.  Use lists of keyword named dictionaries.
  (c.f. Wolffish)
- Provide a separate call for each function.  Return dictionaries (c.f. openATTIC)
- Do not query Ceph directly.  Performance will vary too greatly.  Use other
  modules with Salt mines.
"""

import logging
import sys
import os
import json
import yaml
import urllib
import salt.client
import salt.utils.minions

log = logging.getLogger(__name__)


class Iscsi(object):
    """
    Populating the view requires network interfaces by host, images by pool
    and the current lrbd configuration.
    Saving the choices requires writing out the lrbd.conf
    """

    def __init__(self):
	"""
	Set yaml dumper, initialize Salt client
	"""
	self.data = {}
	self.friendly_dumper = yaml.SafeDumper
	self.friendly_dumper.ignore_aliases = lambda self, data: True
	self.local = salt.client.LocalClient()

    def populate(self):
	"""
	Return the lrbd configuration, interfaces and images.
	"""
	self.data['config'] = self.config()
	self.data['interfaces'] = self.interfaces()
	self.data['images'] = self.images()

	return self.data

    def interfaces(self, wrapped=True):
	"""
	Parse grains for all network interfaces on igw roles.  Possibly
	select public interface.
	"""
	_stdout = sys.stdout
	sys.stdout = open(os.devnull, 'w')

	igws = self.local.cmd("I@roles:igw", 'grains.get', ['ipv4'], expr_form="compound")
	sys.stdout = _stdout
	if wrapped:
	    data = []
	    for igw in igws.keys():
		for addr in igws[igw]:
		    if addr == '127.0.0.1':
			continue
		    data.append({'node': igw, 'addr': addr})
	    return data
	else:
	    for igw in igws.keys():
		igws[igw].remove('127.0.0.1')

	    return igws

    def images(self, wrapped=True):
	"""
	Read a Salt mine of cephimages that lists all images
	and their pools.
	"""
	__opts__ = salt.config.client_config('/etc/salt/master')
	result = salt.utils.minions.mine_get('I@roles:master',
					     'cephimages.list',
					     'compound', __opts__)
	if wrapped:
	    data = []
	    for master in result.keys():
		for pool in result[master]:
		    data.append({'pool': pool, 'img': result[master][pool]})
		break
	    return data
	else:
	    for master in result.keys():
		return result[master]

    def config(self, filename="/srv/salt/ceph/igw/cache/lrbd.conf"):
	"""
	Read the existing lrbd.conf
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

	    # Empty content-type header causes cherrypy to process the request
	    # body as a string.  In such cases, the 'data' argument containing
	    # the lrbd json structure should be URI encoded to prevent
	    # accidental 'arg' substring matching, causing invalid handling
	    # by cherrypy.  Further, a blank content-type is used to avoid
	    # POST preflight checks which would render third party cookie auth
	    # (ie. where the frontend is hosted on a different server than
	    # salt-api) useless.
	    contents = urllib.unquote(kwargs['data']) if 'contenttype' in kwargs and not kwargs['contenttype'] else kwargs['data']

	    with open(filename, 'w') as conf:
		conf.write(contents)
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
	    yml.write(yaml.dump(contents,
				Dumper=self.friendly_dumper,
				default_flow_style=False))
	# refresh pillar
	self.local.cmd("I@roles:master", 'saltutils.pillar_refresh', [''], expr_form="compound")

    def canned_populate(self, canned):
	"""
	Return all canned data

	Note: could add samples from lrbd for config
	"""
	self.data['config'] = self.config()
	self.data['interfaces'] = self.canned_interfaces(canned)
	self.data['images'] = self.canned_images(canned)

	return self.data

    def canned_images(self, canned, wrapped=True):
	"""
	Return canned example for pools and images
	"""
	_images = {1: {'rbd': ['demo1', 'demo2', 'demo3']},
		   2: {'car': ['cement'],
		       'whirl': ['cheese'],
		       'rbd': ['wood', 'writers', 'city'],
		       'swimming': ['cell']}}
	if wrapped:
	    data = []
	    for pool in _images[canned].keys():
		for img in _images[canned][pool]:
		    data.append({'pool': pool, 'img': img})
	    return data
	else:
	    return data[canned]

    def canned_interfaces(self, canned, wrapped=True):
	"""
	Return canned example for nodes and addresses
	"""
	_interfaces = {1: {'igw1': ['192.168.0.2', '192.168.1.2', '192.168.2.2']},
		      2: {'node1': ['10.0.0.10'],
			  'node2': ['10.0.0.11'],
			  'node3': ['10.0.0.12',
				    '172.16.31.12',
				    '192.168.10.112'],
			  'node4': ['1.2.3.4']}}
	if wrapped:
	    data = []
	    for node in _interfaces[canned].keys():
		for addr in _interfaces[canned][node]:
		    data.append({'node': node, 'addr': addr})
	    return data
	else:
	    return _interfaces[canned]


def populate(**kwargs):
    """
    Populate the iSCSI view
    """
    iscsi = Iscsi()
    if 'canned' in kwargs:
	return iscsi.canned_populate(int(kwargs['canned']))
    return iscsi.populate()


def save(**kwargs):
    """
    Save the iSCSI configuration
    """
    iscsi = Iscsi()
    return iscsi.save(**kwargs)


def config():
    """
    Return the iSCSI configuration
    """
    iscsi = Iscsi()
    return iscsi.config()


def interfaces(**kwargs):
    """
    Return the list of interfaces by minion
    """
    iscsi = Iscsi()
    if 'canned' in kwargs:
	return iscsi.canned_interfaces(int(kwargs['canned']), wrapped=False)
    return iscsi.interfaces(wrapped=False)


def images(**kwargs):
    """
    Return the list of images by pool
    """
    iscsi = Iscsi()
    if 'canned' in kwargs:
	return iscsi.canned_images(int(kwargs['canned']), wrapped=False)
    return iscsi.images(wrapped=False)
