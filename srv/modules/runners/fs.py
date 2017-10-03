# -*- coding: utf-8 -*-

# ------------------------------------------------------------------------------
# fs.py
#
# Runner for performing filesystem operations.
# Current task is to create/migrate /var/lib/ceph to btrfs subvolumes if applicable.
#
# ------------------------------------------------------------------------------

import salt.client
import salt.utils.error
import logging
import pprint
import deepsea_minions
import fs

import os
import sys

log = logging.getLogger(__name__)

class Mount(object):
    """
    Structure representing the mount information for a given path.
    """
    def __init__(self, mountpoint, opts):
	self.mountpoint = mountpoint
	# List of mount opts in the form [ x, y, ... , {k : v}, ... ]
	self.opts = opts

    def get_opt(self, opt):
	"""
	Return 'opt' if found in self.opts.  Since self.opts may contain dictionary entries,
	this may return the value of such an entry, should 'opt' match a dictionary entry key.
	"""
	for o in self.opts:
	    if o == opt:
		return o
	    if isinstance(o, dict) and o.has_key(opt):
		return o[opt]

	# Didn't find it.
	return None

    def __str__(self):
	return "{} opts:{}".format(self.mountpoint, self.opts)

class Device(object):
    """
    Structure representing a disk/partition.
    """
    def __init__(self, dev, part_dev, dtype, uuid, fstype):
	# ie. 'vda'
	self.dev = dev
	# ie. 'vda2'
	self.part_dev = part_dev
	# String representing the device type: 'hd', 'ssd', 'unknown'
	self.dtype = dtype
	self.uuid = uuid
	# String representing the underlying fs: 'btrfs', 'xfs', etc
	self.fstype = fstype

    def __str__(self):
	return "uuid:{} (/dev/{}), {}, {}".format(self.uuid, self.part_dev, self.dtype, self.fstype)

class Path(object):
    """
    Structure representing a path on a filesystem.
    """
    def __init__(self, path, attrs, exists, ptype, device, mount):
	# The full path, normalized
	self.path = os.path.normpath(path)
	# lsattr type attributes
	self.attrs = attrs
	self.exists = exists
	# ie. dir or file
	self.ptype = ptype
	# A Device() instance
	self.device = device
	# A Mount() instance
	self.mount = mount

    def __str__(self):
	return "{} {} {}, mounted on: {}, with device info: {}".format("Existent" if self.exists else "Nonexsitent",
					 self.ptype if self.ptype else '', self.path, self.mount, self.device)

# ------------------------------------------------------------------------------
# Runner functions.
# ------------------------------------------------------------------------------

# Some fun output
bold = '\033[1m'
endc = '\033[0m'
green = '\033[1;32m'
yellow = '\033[1;33m'
red = '\033[1;31m'
ceph_statedir = "/var/lib/ceph"

def _analyze_ceph_statedirs(statedirs):
    """
    Based on some elements of statedir, give the admin feedback regarding the ceph variable statedir.
    """
    local = salt.client.LocalClient()
    results = {'ok': [], 'to_create': [], 'to_migrate': [], 'to_correct_cow': [], 'alt_fs': [], 'ceph_down': []}

    for minion, statedir in statedirs.iteritems():
	if statedir.device.fstype == 'btrfs':
	    if statedir.exists:
		# OK, path exists, is there a subvolume mounted on it?
		# We detect this by checking the mountpoint
		if statedir.mount.mountpoint == statedir.path:
		    #subvol = statedir.mount.get_opt('subvol')
		    # Already a subvolume!  Check if CoW
		    if not 'C' in statedir.attrs:
			results['to_correct_cow'].append(minion)
		    else:
			# Copy on write disabled, all good!
			results['ok'].append(minion)
			# Also check to see if Ceph is running.
			if not local.cmd(minion, 'cephprocesses.check', [], expre_form='compound')[minion]:
			    results['ceph_down'].append(minion)
		else:
		    # Path exists, but is not a subovlume
		    results['to_migrate'].append(minion)
	    else:
		# Path does not yet exist.
		results['to_create'].append(minion)
	else:
	    # Not btrfs.  Nothing to suggest.
	    results['alt_fs'].append(minion)
	    # Also check to see if Ceph is running
	    if not local.cmd(minion, 'cephprocesses.check', [], expre_form='compound')[minion]:
		results['ceph_down'].append(minion)

    return results

def create_var(**kwargs):
    local = salt.client.LocalClient()
    path = ceph_statedir
    ret = True

    statedirs = _inspect_ceph_statedir(path)
    results = _analyze_ceph_statedirs(statedirs)

    if not results['to_create']:
	print "{}No nodes marked for subvolume creation.{}".format(bold, endc)
	return True

    for m in results['to_create']:
	if ret:
	    print "{}{}: Beginning creation...{}".format(bold, m, endc)
	    for minion, ret in local.cmd(m, 'fs.instantiate_btrfs_subvolume',
					 ["path={}".format(path), "subvol=@{}".format(path)],
					 expr_form='compound').iteritems():
		if not ret:
		    print ("{}{}: {}Failed to properly create and mount @{} onto {}{}.  {}Check the local "
			   "minion logs for further details.{}".format(bold, minion, red, path, path, endc, bold, endc))
		else:
		    print ("{}{}: {}Successfully created and mounted @{} onto {}.{}".format(
			bold, minion, green, path, path, endc))
		    ret = _correct_ceph_statedir_attrs(minion)

    if ret:
	print "{}Success.{}".format(green, endc)
    else:
	print "{}Failure detected, not proceeding with further creations.{}".format(red, endc)

    return ret

def migrate_var(**kwargs):
    """
    Drive the migration of /var/lib/ceph to a btrfs subvolume.  This needs to be done one node at a time.
    """
    local = salt.client.LocalClient()
    path = ceph_statedir
    ret = True

    statedirs = _inspect_ceph_statedir(path)
    results = _analyze_ceph_statedirs(statedirs)

    if not results['to_migrate']:
	print "{}No nodes marked for subvolume migration.{}".format(bold, endc)
	return True

    for m in results['to_migrate']:
	if ret:
	    print "{}{}: Beginning migration...{}".format(bold, m, endc)
	    for minion, ret in local.cmd(m, 'fs.migrate_path_to_btrfs_subvolume',
					 ["path={}".format(path), "subvol=@{}".format(path)],
					 expr_form='compound').iteritems():
		# Human intervention needed.
		if ret == None:
		    print ("{}{}: {}Failure detected while migrating {} to btrfs subvolume.  This failure is "
			   "potentially serious and will require manual intervention on the node to "
			   "determine the cause.  Please check /var/log/salt/minion, the status "
			   "of Ceph daemons and the state of {}.  You may also run: {}{}salt-run fs.inspect_var "
			   "{}{}to check the status.{}".format(
			       bold, minion, red, path, path, endc, bold, endc, red, endc))
		elif ret == False:
		    print ("{}{}: {}Failure detected while migrating {} to btrfs subvolume.  We have failed to properly "
			   "migrate {}, however, we have hopefully recovered to the previous state and Ceph "
			   "should again be running.  Please, however check /var/log/salt/minion, "
			   "the status of Ceph daemons and the state of {} to confirm.  You may also run: "
			   "{}{}salt-run fs.inspect_var {}{}to check the status.{}".format(
			       bold, minion, yellow, path, path, path, endc, bold, endc, yellow, endc))
		else:
		    print "{}{}: {}Successfully migrated.{}".format(bold, minion, green, endc)
		    ret = _correct_ceph_statedir_attrs(m)

    if ret:
	print "{}Success.{}".format(green, endc)
    else:
	print "{}Failure detected, not proceeding with further migrations.{}".format(red, endc)

    return ret

def _correct_ceph_statedir_attrs(minion=None):
    """
    Helper function to disable the copy-on-write attr on the ceph statedir.
    """
    local = salt.client.LocalClient()
    path = ceph_statedir
    attrs = "C"
    recursive = True
    ret = True

    if minion:
	# Omit /var/lib/ceph/osd directory, as underneath we may have OSDs mounted.
	for minion, rets in local.cmd(minion, 'fs.add_attrs',
				      ["path={}".format(path), "attrs={}".format(attrs),
				       "rec={}".format(recursive), "omit={}/osd".format(path)],
				      expr_form='compound').iteritems():
	    for p, ret in rets.iteritems():
		if not ret:
		    print ("{}{}: {}Failed to recursively disable copy-on-write for {}.{}".format(bold, minion, red, p, endc))
		    ret = False

	if ret:
	    print ("{}{}: {}Successfully disabled copy-on-write for {} and it's contents.{}".format(bold, minion, green, path, endc))

    return ret

def correct_var_attrs(**kwargs):
    """
    Recursively set No_COW (ie. disable copy-on-write) flag on /var/lib/ceph.
    """
    local = salt.client.LocalClient()
    path = ceph_statedir
    recursive = True
    ret = True

    all_btrfs_nodes = kwargs['all_btrfs_nodes'] if kwargs.has_key('all_btrfs_nodes') else False

    statedirs = _inspect_ceph_statedir(path)
    results = _analyze_ceph_statedirs(statedirs)

    if not all_btrfs_nodes and not results['to_correct_cow']:
	print "{}No nodes marked for copy-on-write correction.{}".format(bold, endc)
	return True

    # If all_btrfs_nodes == True, correct COW on all nodes regardless whether they're in results['to_correct_cow'].
    # Only really useful if the admin manually set No_COW on /var/lib/ceph, but didn't recursively set all
    # files underneath.
    for minion, statedir in statedirs.iteritems():
	if not statedir.exists:
	    print "{}{}: {} not found.{}".format(bold, minion, path, endc)

	if statedir.exists and statedir.device.fstype == 'btrfs':
	    minion_to_correct = None
	    if all_btrfs_nodes:
		minion_to_correct = minion
	    else:
		minion_to_correct = minion if minion in results['to_correct_cow'] else None

	    # Unlike the creation and migration functions, don't abort on first failure.
	    if not _correct_ceph_statedir_attrs(minion_to_correct):
		ret = False

    if ret:
	print "{}Success.{}".format(green, endc)
    else:
	print "{}Failure detected disabling copy-on-write for {}.{}".format(red, path, endc)

    return ret

def _inspect_ceph_statedir(path):
    """
    Helper function that collects /var/lib/ceph information from all minions.

    Returns a dictionary of Path objects keyed on minion id.

    """
    target = deepsea_minions.DeepseaMinions()
    search = target.deepsea_minions
    local = salt.client.LocalClient()

    # A container of Path's keyed on minion id.
    statedirs = {}


    for minion, path_info in local.cmd(search, 'fs.inspect_path',
				       ["path={}".format(path)],
				       expr_form='compound').iteritems():
	statedirs[minion] = Path(path, path_info['attrs'], path_info['exists'], path_info['type'],
				 Device(path_info['dev_info']['dev'], path_info['dev_info']['part_dev'],
					path_info['dev_info']['type'], path_info['dev_info']['uuid'],
					path_info['dev_info']['fstype']),
				 Mount(path_info['mount_info']['mountpoint'], path_info['mount_info']['opts'])) if path_info['ret'] else None

    return statedirs

def inspect_var(**kwargs):
    """
    Collect /var/lib/ceph information from all minions.
    """
    path = ceph_statedir

    # Loud by default.
    quiet = kwargs['quiet'] if kwargs.has_key('quiet') else False

    statedirs = _inspect_ceph_statedir(path)
    results = _analyze_ceph_statedirs(statedirs)

    if not quiet:
	print "{}Inspecting Ceph Statedir ({})...{}".format(bold, path, endc)
	for minion, statedir in statedirs.iteritems():
	    print "{}{}:{} {}".format(bold, minion, endc, statedir)
	print ""

    if not quiet:
	# Offer some suggestions.
	# Migration/Creation/COW adjustment.

	if results['ceph_down']:
	    print "{}The following nodes have Ceph processes which are currently down:{}".format(red, endc)
	    for minion in results['ceph_down']:
		print "{}".format(minion)
	    print "{}Determine the nature of the failures before proceeding.{}\n".format(red, endc)

	if results['to_migrate']:
	    print "{}For the following nodes using btrfs:{}".format(yellow, endc)
	    for minion in results['to_migrate']:
		print "{}".format(minion)
	    print ("{}{} exists, but no btrfs subvolume is mounted.  "
		   "Run: {}{}salt-run fs.migrate_var{}{} to "
		   "migrate {} to the btrfs subvolume @{}{}".format(yellow, path, endc, bold, endc, yellow, path, path, endc))
	    print ("{}You may then run: {}{}salt-run fs.inspect_var {}{}to check the "
		   "status.{}\n".format(yellow, endc, bold, endc, yellow, endc))
	else:
	    #print "{}No nodes found needing migration of {} to btrfs subvolume @{}.{}\n".format(green, path, path, endc)
	    pass

	if results['to_create']:
	    print "{}For the following nodes using btrfs:{}".format(yellow, endc)
	    for minion in results['to_create']:
		print "{}".format(minion)
	    print ("{}{} does not yet exist.  "
		   "Run: {}{}salt-run fs.create_var{}{} to create and mount "
		   "the btrfs subvolume @{} onto {}.{}".format(yellow, path, endc, bold,
							       endc, yellow, path, path, endc))
	    print ("{}You may then run: {}{}salt-run fs.inspect_var {}{}to check the "
		   "status.{}\n".format(yellow, endc, bold, endc, yellow, endc))
	else:
	    # Migration also creates subvolumes, so let's not confuse the admin.
	    if not results['to_migrate']:
		#print "{}No nodes found needing creation of {} as btrfs subvolume @{}.{}\n".format(green, path, path, endc)
		pass

	if results['to_correct_cow']:
	    print "{}For the following nodes using btrfs:{}".format(yellow, endc)
	    for minion in results['to_correct_cow']:
		print "{}".format(minion)
	    print ("{}A btrfs subvolume is mounted on {}.  However, copy-on-write is enabled.  Run: "
		   "{}{}salt-run fs.correct_var_attrs{}{} to disable copy-on-write.".format(
		       yellow, path, endc, bold, endc, yellow, endc))
	    print ("{}You may then run: {}{}salt-run fs.inspect_var {}{}to check "
		   "the status.{}\n".format(yellow, endc, bold, endc, yellow, endc))
	else:
	    # Migration also sets No_COW, so let's not confuse the admin.
	    if not results['to_migrate']:
		print "{}No nodes found needing adjustment of copy-on-write for {}.{}".format(green, path, endc)
		print ("{}NOTE: If copy-on-write was disabled manually for {}, you may still want to run "
		       "{}{}salt-run fs.correct_var_attrs all_btrfs_nodes=True{}{} to correct all "
		       "relevant files contained within {} on all nodes running btrfs.{}\n".format(
			   yellow, path, endc, bold, endc, yellow, path, endc))

	if results['ok']:
	    print "{}The following btrfs nodes have @{} correctly mounted on {}, and do not require any subvolume manipulation:{}".format(green, path, path, endc)
	    for minion in results['ok']:
		print "{}".format(minion)
	    print ""

	if results['alt_fs']:
	    print "{}The following nodes are not using btrfs, and hence no action is needed:{}".format(green, endc)
	    for minion in results['alt_fs']:
		print "{}".format(minion)
	    print ""

    return True

def help():
    """
    Usage.
    """
    usage = ("salt-run fs.inspect_var\n\n"
	     "    Inspects /var/lib/ceph, provides mountpoint and device information along with suggestions regarding "
	     "migration of /var/lib/ceph to a btrfs subvolume if applicable.\n"
	     "\n\n"
	     "salt-run fs.create_var\n\n"
	     "    Creates /var/lib/ceph (if not yet present) as a btrfs subvolume.\n"
	     "\n\n"
	     "salt-run fs.migrate_var\n\n"
	     "    Migrates /var/lib/ceph to a btrfs subvolume (@/var/lib/ceph) if applicable.\n"
	     "\n\n"
	     "salt-run fs.correct_var_attrs [all_btrfs_nodes=True]\n\n"
	     "    Disables copy-on-write for /var/lib/ceph on btrfs if applicable.\n"
	     "\n\n")
    print usage
    return ""
