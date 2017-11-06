# -*- coding: utf-8 -*-
# pylint: disable=modernize-parse-error,anomalous-backslash-in-string
"""
This runner is the complement to the populate.proposals runner.

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
    any profile-* directories represent a specific OSD
    assignment for a particular chassis.  All sls and yaml files are
    included for a given hardware profile.

For automation, an optional fifth part is

Customization:
    a custom subdirectory that may be present as part of the provisioning.
    This entry is last and will overwrite any of the contents of the sls or
    yaml files.

    Note that this type of customization is redundant with specifying the
    desired values in /srv/pillar/ceph/stack directory tree and likely
    unnecessary.  This will still work and may prove useful for some.

All files are overwritten in the destination tree /srv/pillar/ceph/stack/default.

"""

import os
import errno
import glob
import logging
import imp
import re
import shutil
import yaml

CUR_FILE_PATH = os.path.dirname(os.path.realpath(__file__))
STACK_PATH = os.path.abspath('{}/../pillar/stack.py'.format(CUR_FILE_PATH))
STACK = imp.load_source('pillar.stack', STACK_PATH)
log = logging.getLogger(__name__)


def help_():
    """
    Usage
    """
    usage = ('salt-run push.proposal:\n\n'
             '    Reads the policy.cfg and generates the Salt configuration\n'
             '\n\n'
             'salt-run push.convert:\n\n'
             '    Converts the hardware profiles from filestore to bluestore\n'
             '\n\n')
    print usage
    return ""


def proposal(filename="/srv/pillar/ceph/proposals/policy.cfg", dryrun=False):
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


def convert(filename="/srv/pillar/ceph/proposals/policy.cfg"):
    """
    Convert the hardware profiles that policy.cfg is using and update
    the policy.cfg.

    Note: While the call "push.convert" does not make much sense, this
    runner contained most of the necessary logic
    """
    if not os.path.isfile(filename):
        log.warning("{} is missing - nothing to migrate".format(filename))
        return ""
    if os.path.isfile("{}-original".format(filename)):
        log.error("Already migrated - remove {}-original before rerunning".format(filename))
        return ""
    pillar_data = PillarData()
    common = pillar_data.organize(filename)
    pillar_data.convert(common)
    rename(filename)

    proposal(filename=filename)
    return ""


def _create_dirs(path, root):
    """
    Verbose mkdir
    """
    try:
        os.makedirs(path)
    except OSError as err:
        if err.errno == errno.EACCES:
            log.exception('''
            ERROR: Cannot create dir {}
            Please make sure {} is owned by salt
            '''.format(path, root))
            raise err


class PillarData(object):
    """
    Imagine if rsync could merge the contents of YAML files.  Combine
    the specified files from the proposals tree and populate the pillar
    tree.
    """

    def __init__(self, dryrun=False):
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

        self._clean()

        for pathname in common.keys():
            merged = _merge(pathname, common)
            filename = self.pillar_dir + "/" + pathname
            self._default(filename, merged)

            if pathname.startswith("cluster"):
                # Use the entire list of minions under cluster to populate
                # stack/{cluster_name}/minions.  Skip unassigned.
                if merged['cluster'] != "unassigned":
                    newpath = re.sub(r'sls', 'yml', pathname)
                    relative = re.sub(r'cluster',
                                      "stack/{}/minions".format(merged['cluster']), newpath)
                    custom = (self.pillar_dir + "/" + relative)
                    self._custom(custom)

            if pathname.startswith("stack"):
                # Mirror the default tree
                default_path = re.sub(r'stack/default', "stack", pathname)
                custom = self.pillar_dir + "/" + default_path
                self._custom(custom)

    def convert(self, common):
        """
        Process all hardware profiles
        """
        for pathname in common.keys():
            for filename in common[pathname]:
                if 'profile-' in filename:
                    with open(filename, "r") as yml:
                        content = yaml.safe_load(yml)
                    migrated = _migrate(content, filename)
                    newfilename = re.sub('profile-', 'migrated-profile-', filename)
                    path_dir = os.path.dirname(newfilename)
                    _create_dirs(path_dir, self.pillar_dir)
                    with open(newfilename, "w") as yml:
                        yml.write(yaml.dump(migrated,
                                  Dumper=self.friendly_dumper,
                                  default_flow_style=False))

    def _clean(self):
        """
        Remove the stack/default tree to remove any leftover files from a
        previous removal
        """
        stack_default = "{}/stack/default".format(self.pillar_dir)
        if os.path.isdir(stack_default):
            shutil.rmtree(stack_default)

    def _default(self, filename, merged):
        """
        Output the merged contents to the default tree
        """
        path_dir = os.path.dirname(filename)
        if not os.path.isdir(path_dir):
            _create_dirs(path_dir, self.pillar_dir)
        log.info("Writing {}".format(filename))
        if not self.dryrun:
            with open(filename, "w") as yml:
                yml.write(yaml.dump(merged,
                          Dumper=self.friendly_dumper,
                          default_flow_style=False))

    def _custom(self, custom):
        """
        Create commented files to let the admin know where it's safe
        to make custom changes.  Mirror the default tree. Never overwrite.
        """
        path_dir = os.path.dirname(custom)
        if not os.path.isdir(path_dir):
            _create_dirs(path_dir, self.pillar_dir)
        if not self.dryrun:
            if not os.path.isfile(custom):
                log.info("Writing {}".format(custom))
                with open(custom, "w") as yml:
                    custom_split = custom.split("stack")
                    custom_for = "{}{}{}".format(
                            custom_split[0],
                            "stack/default",
                            custom_split[1])
                    yml.write("# {}\n".format(custom))
                    yml.write("# Overwrites configuration in {}\n".format(custom_for))
                    _examples(custom, yml)

    def organize(self, filename):
        """
        Associate all filenames with their common subdirectory.
        """
        common = {}
        with open(filename, "r") as policy:
            for line in policy:
                # strip comments from the end of the line
                line = re.sub(r'\s+#.*$', '', line)
                line = line.strip()
                if line.startswith('#') or not line:
                    log.debug("Ignoring '{}'".format(line))
                    continue
                files = _parse(self.proposals_dir + "/" + line)
                if not files:
                    log.warning("{} matched no files".format(line))
                log.debug(line)
                log.debug(files)
                for filename in files:
                    if os.stat(filename).st_size == 0:
                        log.warning("Skipping empty file {}".format(filename))
                        continue
                    if os.path.isfile(filename):
                        pathname = _shift_dir(filename.replace(self.proposals_dir, ""))
                        if pathname not in common:
                            common[pathname] = []
                        common[pathname].append(filename)
                    else:
                        log.warning("{} does not exist".format(filename))

        # This should be in a conditional, but
        # getEffectiveLevel returns 1 no matter setting
        for pathname in sorted(common):
            log.debug(pathname)
            for filename in common[pathname]:
                log.debug("    {}".format(filename))
        return common


def _migrate(yml, filename):
    """
    Migrate the original data structure to the ceph namespace data
    structure
    """
    if 'storage' in yml and 'osds' in yml['storage']:
        yml['ceph'] = {}
        yml['ceph']['storage'] = {}
        yml['ceph']['storage']['osds'] = {}
        for osd in yml['storage']['osds']:
            yml['ceph']['storage']['osds'][osd] = {'format': 'bluestore'}
        for entry in yml['storage']['data+journals']:
            for osd, journal in entry.iteritems():
                yml['ceph']['storage']['osds'][osd] = {'format': 'bluestore',
                                                       'wal': journal,
                                                       'db': journal}
        yml.pop('storage')
    elif 'ceph' in yml and 'storage' in yml['ceph'] and 'osds' in yml['ceph']['storage']:
        # if the profile is already in the new ceph namespace, just flip it to bluestore
        for osd in yml['ceph']['storage']['osds']:
            if yml['ceph']['storage']['osds'][osd]['format'] != 'filestore':
                continue
            yml['ceph']['storage']['osds'][osd]['format'] = 'bluestore'
            if 'journal' not in yml['ceph']['storage']['osds'][osd]:
                continue
            if yml['ceph']['storage']['osds'][osd]['journal'] != osd:
                # journal on separate device, set up wal and db to point to it
                cso = yml['ceph']['storage']['osds']
                cso[osd]['wal'] = cso[osd]['journal']
                cso[osd]['db'] = cso[osd]['journal']
            # get rid of the old journal item
            yml['ceph']['storage']['osds'][osd].pop('journal')
    else:
        log.info("No migration for {} - copying".format(filename))
    return yml


def rename(filename):
    """
    Copy the policy.cfg and update the existing file
    """
    shutil.copyfile(filename, "{}-original".format(filename))
    lines = []
    with open(filename, "r") as policy:
        for line in policy:
            if line.startswith('profile-'):
                line = "migrated-{}".format(line)
            lines.append(line)
    with open(filename, "w") as policy:
        policy.write("".join(lines))


def _examples(custom, yml):
    """
    Provide commented examples for admin convenience
    """
    if 'cluster.yml' in custom:
        text = '''
          #rgw_configurations:
          #  rgw:
          #    users:
          #      - { uid: "demo", name: "Demo", email: "demo@demo.nil" }
          #      - { uid: "demo1", name: "Demo1", email: "demo1@demo.nil" }
          '''
        text = re.sub(re.compile("^ {14}", re.MULTILINE), "", text)
        yml.write(text)


def _merge(pathname, common):
    """
    Merge the files via stack.py
    """
    merged = {}
    for filename in common[pathname]:
        with open(filename, "r") as content:
            content = yaml.safe_load(content)
            # pylint: disable=protected-access
            merged = STACK._merge_dict(merged, content)
    return merged


def _parse(line):
    """
    Return globbed files constrained by optional slices or regexes.
    """
    if " " in line:
        parts = re.split('\s+', line)
        files = sorted(glob.glob(parts[0]))
        for optional in parts[1:]:
            filter_type, value = optional.split('=')
            if filter_type == "re":
                regex = re.compile(value)
                files = [m.group(0) for l in files for m in [regex.search(l)] if m]
            elif filter_type == "slice":
                # pylint: disable=eval-used
                files = eval("files{}".format(value))
            else:
                log.warning("keyword {} unsupported".format(filter_type))

    else:
        files = glob.glob(line)
    return files


def _shift_dir(path):
    """
    Remove the leftmost directory, expects beginning /
    """
    return "/".join(path.split('/')[2:])

__func_alias__ = {
                 'help_': 'help',
                 }
