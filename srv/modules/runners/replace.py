# -*- coding: utf-8 -*-
# pylint: disable=too-few-public-methods,modernize-parse-error
"""
Runner to remove a single osd
"""

from __future__ import absolute_import
from __future__ import print_function
import time
import logging
import os
import yaml

# pylint: disable=import-error,3rd-party-module-not-gated,redefined-builtin
import salt.client
import salt.runner

log = logging.getLogger(__name__)


def help_():
    """
    Usage
    """
    usage = (
        "salt-run replace.osd id [id ...][force=True][timeout=value][delay=value]:\n\n"
        "    Removes an OSD from a minion\n"
        "\n\n"
    )
    print(usage)
    return ""


def osd(*args, **kwargs):
    """
    Remove an OSD gracefully or forcefully on the minion

    Note: If I were not in Salt, this whole routine would become a library.
    This runner can be called by remove.osd and is only different by three
    commands.  However, we have one runner call and multiple module calls below.
    Trying to refactor these module calls into a __utils__ would require yet
    another module.  Debugging all of this at runtime would be add to the fun,
    so I didn't.
    """
    # Parameters for osd.remove module
    supported = ["force", "timeout", "delay"]
    passed = ["{}={}".format(k, v) for k, v in kwargs.items() if k in supported]
    log.debug("Converted kwargs: {}".format(passed))
    context = kwargs.get('remove', 'replace')

    # OSDs to remove
    osds = list(str(arg) for arg in args)
    if _checks_failed(osds, kwargs):
        return ""

    master_minion = _master_minion()

    local = salt.client.LocalClient()
    host_osds = local.cmd("I@roles:storage", "osd.list", tgt_type="compound")
    assert isinstance(host_osds, dict)

    for osd_id in osds:
        host = _find_host(osd_id, host_osds)
        if host:
            grains = local.cmd(host, "grains.get", ["ceph"], tgt_type="compound")
            msg = _remove_osd(local, master_minion, osd_id, passed, host)
            if msg:
                print("{}\nFailed to remove osd {}".format(msg, osd_id))
                osds.remove(osd_id)
                continue

            # Rename minion profile
            minion_profile(host, osds, grains, context)

    if "called" in kwargs and kwargs["called"]:
        # Return for remove.osd
        return {"master_minion": master_minion, "osds": osds}
    return ""


def _checks_failed(osds, kwargs):
    """
    Check the safety, argument length.  Pause when multiple arguments are
    passed to allow the admin to abort incorrect shell expansions
    """
    # Checks
    if not __salt__["disengage.check"]():
        log.error('Safety engaged...run "salt-run disengage.safety"')
        return True

    if len(osds) < 1:
        help_()
        return True

    if len(osds) > 1:
        # Pause for a moment, let the admin see what they passed
        print(
            "Removing osds {} from minions\nPress Ctrl-C to abort".format(
                ", ".join(osds)
            )
        )
        pause = 5
        if "pause" in kwargs and kwargs["pause"]:
            pause = kwargs["pause"]
        time.sleep(pause)

    return False


def _remove_osd(local, master_minion, osd_id, passed, host):
    """
    Set OSD to out, remove OSD from minion
    """
    local.cmd(
        master_minion,
        "cmd.run",
        ["ceph osd out {}".format(osd_id)],
        tgt_type="compound",
    )

    print("Removing osd {} from minion {}".format(osd_id, host))
    msg = local.cmd(host, "osd.remove", [osd_id] + passed)[host]
    while msg.startswith("Timeout"):
        print("  {}\nRetrying...".format(msg))
        msg = local.cmd(host, "osd.remove", [osd_id] + passed)[host]
    return msg


def _master_minion():
    """
    Load the master modules
    """
    __master_opts__ = salt.config.client_config("/etc/salt/master")
    __master_utils__ = salt.loader.utils(__master_opts__)
    __salt_master__ = salt.loader.minion_mods(__master_opts__, utils=__master_utils__)

    return __salt_master__["master.minion"]()


def _find_host(osd_id, host_osds):
    """
    Search lists for ID, return host
    """
    for host in host_osds:
        if str(osd_id) in host_osds[host]:
            return host
    return ""


def minion_profile(minion, osds, grains, context):
    """
    Rename a minion profile to indicate that the minion profile needs to be
    recreated if the replace context is given
    Delete the entry in the minion's profile if the remove context is given

    Note: Nobody is required to have profile entries in the policy.cfg.  Some
    might be modifying their pillar data directly.  Also, the file will
    not exist when called for multiple replacements.  Lastly, minions may
    belong to more than one hardware profile.  Each must be renamed.
    """
    files = __salt__["push.organize"]()
    local = salt.client.LocalClient()
    disks = local.cmd(minion, "cephdisks.list", tgt_type="compound")[minion]

    yaml_file = "stack/default/ceph/minions/{}.yml".format(minion)
    if yaml_file in files:
        for filename in files[yaml_file]:
            if os.path.exists(filename):
                if context == 'replace':
                    try:
                        print("Renaming minion {} profile".format(minion))
                        os.rename(filename, "{}-replace".format(filename))
                        _insert_replace_flag(
                            grains, disks, minion, osds, "{}-replace".format(filename)
                        )
                    # pylint: disable=bare-except
                    except:
                        log.error("Failed to rename minion {} profile".format(minion))
                        os.rename("{}-replace".format(filename), filename)
                elif context == 'remove':
                    try:
                        print("Removing osd entry from {} profile".format(minion))
                        _remove_osd_entry(grains, disks, minion, osds, filename)
                    # pylint: disable=bare-except
                    except:
                        # pylint: disable=line-too-long
                        log.error("Failed to remove osd entry from minion {} profile".format(minion))
                else:
                    print('Unknown context {}'.format(context))
                    return False

    return ""


def _map_grains_proposal_disk(grains_disk, disks, content):
    """
    Compare grains to proposal to find the correct path for the disk

    This makes use of cephdisks.list as a base that has different names ("Device Files")
    1. iterate over cephdisks.list output
    2. check if the disk that is written in the grain matches the current disk
    3. if it matches, look for the disk-path that is used in the proposal
    4. add that disk-path the the list of paths
    5. return list
    """

    for disk in disks:
        if grains_disk in disk["Device Files"]:
            for prop_disk in content["ceph"]["storage"]["osds"]:
                if prop_disk in disk["Device Files"]:
                    return prop_disk
    return None


def _insert_replace_flag(grains, disks, minion, osds, filename):
    """ Insert 'replace: true' into proposal file for all osds that are passed in """

    with open(filename, "rb") as proposal_file:
        content = yaml.safe_load(proposal_file)

    paths_to_flag = _get_profile_keys(osds, grains, minion, disks, content)

    for path in paths_to_flag:
        content["ceph"]["storage"]["osds"][path]["replace"] = True

    with open(filename, "w") as proposal_file:
        yaml.dump(content, proposal_file, default_flow_style=False)


def _remove_osd_entry(grains, disks, minion, osds, filename):
    """ Delete osd entry in proposal for all osds that are passed in """

    with open(filename, "rb") as proposal_file:
        content = yaml.safe_load(proposal_file)

    paths_to_remove = _get_profile_keys(osds, grains, minion, disks, content)

    for path in paths_to_remove:
        del content["ceph"]["storage"]["osds"][path]

    with open(filename, "w") as proposal_file:
        yaml.dump(content, proposal_file, default_flow_style=False)


def _get_profile_keys(osds, grains, minion, disks, content):
    """ Extract keys that match a key in the profile """
    profile_keys = []
    for osd_id in osds:
        if str(osd_id) in grains[minion]:
            osd_partition = grains[minion][str(osd_id)]["partitions"]["osd"]
            grains_disk = osd_partition.rstrip("0123456789").replace("-part", "")
            profile_keys.append(_map_grains_proposal_disk(grains_disk, disks, content))
    return profile_keys


__func_alias__ = {"help_": "help"}
