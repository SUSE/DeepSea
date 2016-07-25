#!/usr/bin/python

import os
import glob
import yaml
import pprint
import logging
import imp
import re

"""
This runner is the complement to the populate.proposals. 

The policy.cfg only includes matching files.  The admin may use globbing
or specific filenames.  Comments and blank lines are ignored.  The file
is expected to be created by hand currently, although the intent is to 
provide examples for different strategies.  To avoid globbing entirely
and manually create the file in a single command, run

find * -name \*.sls -o -name \*.yml | sort > policy.cfg

Proceed to remove all undesired assignments or consolidate lines into 
equivalent globbing patterns.

The four parts are 

Common configuration:  
    any yaml files in the config tree.  These files contain data needed for
    any cluster.
Cluster assignment: 
    any cluster-* directories contain sls files assigning specific minions
    to specific clusters.  The cluster-unassigned will make Salt happy and
    conveys the explicit intent that a minion is not part of a Ceph cluster.
Role assignment:
    any role-* directories contain sls files and stack related yaml files.
    One or more roles can be included for any minion.  
Hardware profile:
    any directory beginning with a number represents a specific OSD 
    assignment for a particular chassis.  All sls and yaml files are
    included for a given hardware profile.

For automation, an optional fifth part is

Customization:
    a custom subdirectory that may be present as part of the provisioning.
    This entry is last and will overwrite any of the contents of the sls or 
    yaml files.

All files are currently overwritten in the destination tree.
    
"""

stack = imp.load_source('pillar.stack', '/srv/modules/pillar/stack.py')
log = logging.getLogger(__name__)


def proposal(filename = "/srv/pillar/ceph/proposals/policy.cfg", dryrun = False):
    """
    Read the passed filename, organize the files with common subdirectories
    and output the merged contents into the pillar.
    """
    if not os.path.isfile(filename):
        log.warning("{} is missing - nothing to push".format(filename))
        return True
    pillar_data = PillarData(dryrun)
    common = pillar_data.organize(filename)
    pillar_data.output(common)
    return True
    

class PillarData(object):
    """
    Imagine if rsync could merge the contents of YAML files.  Combine
    the specified files from the proposals tree and populate the pillar
    tree.
    """

    def __init__(self, dryrun):
        """
        The source is proposals_dir and the destination is pillar_dir
        """
        self.proposals_dir = "/srv/pillar/ceph/proposals"
        self.pillar_dir = "/srv/pillar/ceph"
        self.dryrun = dryrun

        # Keep yaml human readable/editable
        self.friendly_dumper = yaml.SafeDumper
        self.friendly_dumper.ignore_aliases = lambda self, data: True

    def output(self, common):
        """
        Write the merged YAML files to the correct locations, 
        /srv/pillar/ceph/cluster and /srv/pillar/ceph/stack/default.
        """
    
        for pathname in common.keys():
            merged = self._merge(pathname, common)
            filename = self.pillar_dir + "/" + pathname
            self._default(filename, merged)

            if pathname.startswith("cluster"):
                # Use the entire list of minions under cluster to populate
                # stack/{cluster_name}/minions.  Skip unassigned.
                if merged['cluster'] != "unassigned":
                    custom = self.pillar_dir + "/" + re.sub(r'cluster', "stack/{}/minions".format(merged['cluster']), re.sub(r'sls', 'yml', pathname)) 
                    self._custom(custom)
            

            if pathname.startswith("stack"):
                # Mirror the default tree
                default_path = re.sub(r'stack/default', "stack", pathname) 
                custom = self.pillar_dir + "/" + default_path
                self._custom(custom)

    def _default(self, filename, merged):
        """
        Output the merged contents to the default tree
        """
        path_dir = os.path.dirname(filename)
        if not os.path.isdir(path_dir):
            os.makedirs(path_dir)
        log.info("Writing {}".format(filename))
        if not self.dryrun:
            with open(filename, "w") as yml:
                yml.write(yaml.dump(merged, Dumper=self.friendly_dumper,
                                                  default_flow_style=False))

    def _custom(self, custom):
        """
        Create commented files to let the admin know where it's safe
        to make custom changes.  Mirror the default tree. Never overwrite.
        """
        path_dir = os.path.dirname(custom)
        if not os.path.isdir(path_dir):
            os.makedirs(path_dir)
        if not self.dryrun:
            if not os.path.isfile(custom):
                log.info("Writing {}".format(custom))
                with open(custom, "w") as yml:
                    yml.write("# Customizations for {}\n".format(custom))
    
    
    def _merge(self, pathname, common):
        """
        Merge the files via stack.py
        """
        merged = {}
        for filename in common[pathname]:
            with open(filename, "r") as content:
                content = yaml.safe_load(content)
                merged = stack._merge_dict(merged, content)
        return merged
        
    
    
    def organize(self, filename):
        """
        Associate all filenames with their common subdirectory.
        """
        common = {}
        with open(filename, "r") as policy:
            for line in policy:
                # Possibly support kwargs as additional parameters
                # This would allow regex and slicing of the globbed filenames
                line = line.rstrip()
                if (line.startswith('#') or not line):
                    log.debug("Ignoring '{}'".format(line))
                    continue
                #files = glob.glob(self.proposals_dir + "/" + line)
                files = self._parse(self.proposals_dir + "/" + line)
                if not files:
                    log.warning("{} matched no files".format(line))
                log.debug(line)
                log.debug(files)
                for filename in files:
                    if os.path.isfile(filename):
                        pathname = self._shift_dir(filename.replace(self.proposals_dir, ""))
                        if not pathname in common:
                            common[pathname] = []
                        common[pathname].append(filename)
                    else:
                        log.warning("{} does not exist".format(filename))

        # This should be in a conditional, but
        # getEffectiveLevel returns 1 no matter setting
        for pathname in sorted(common.keys()):
            log.debug(pathname)
            for filename in common[pathname]:
                log.debug("    {}".format(filename))
        return common
    
    
    def _parse(self, line):
        """
        Return globbed files constrained by optional slices or regexes.
        """
        if " " in line:
            parts = re.split('\s+', line)
            files = sorted(glob.glob(parts[0]))
            for kv in parts[1:]:
                k, v = kv.split('=')
                if k == "re":
                    regex = re.compile(v)
                    files = [m.group(0) for l in files for m in [regex.search(l)] if m]
                elif k == "slice":
                    files = eval("files{}".format(v))
                else:
                    log.warning("keyword {} unsupported", k) 
                
        else:
            files = glob.glob(line)
        return files


    def _shift_dir(self, path):
        """
        Remove the leftmost directory, expects beginning /
        """
        return "/".join(path.split('/')[2:])
            
    
