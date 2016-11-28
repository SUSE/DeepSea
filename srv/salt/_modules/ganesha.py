#!/usr/bin/python

import os

def configure():
	'''
	- Systemctl use gansha.conf as default conf. 
	- Create symbolic link between ceph.conf and ganesha.conf
	'''
	os.rename('/etc/ganesha/ganesha.conf','/etc/ganesha/ganesha.conf.orig')
	os.symlink('/etc/ganesha/ceph.conf','/etc/ganesha/ganesha.conf')