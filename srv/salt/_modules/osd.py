#!/usr/bin/python

import os
import glob
import rados
import json
import logging
import time
import re
from subprocess import call, Popen, PIPE

log = logging.getLogger(__name__)

def paths():
    """
    Return an array of pathnames
    """
    return [ pathname for pathname in glob.glob("/var/lib/ceph/osd/*") ]

def devices():
    """
    Return an array of devices
    """
    paths = [ pathname for pathname in glob.glob("/var/lib/ceph/osd/*") ]
    devices = []
    with open('/proc/mounts') as mounts:
        for line in mounts:
            device, path = line.split()[:2]
            if path in paths:
                devices.append(device)

    return devices

def pairs():
    """
    Return an array of devices and paths
    """
    paths = [ pathname for pathname in glob.glob("/var/lib/ceph/osd/*") ]
    pairs = []
    with open('/proc/mounts') as mounts:
        for line in mounts:
            partition, path = line.split()[:2]
            if path in paths:
                m = re.match(r'([a-z/]+).*', partition)
                device = m.group(1)
                pairs.append([ device, path ])

    return pairs


def list():
    """
    Return the array of ids.
    """
    return [ path.split('-')[1] for path in glob.glob("/var/lib/ceph/osd/*") if '-' in path ]
   
def ids():
    """
    Synonym for list
    """
    return list()

class OSDWeight(object):
    """
    """

    def __init__(self, id, **kwargs):
        """
        Initialize settings, connect to Ceph cluster
        """
        self.id = id
        self.settings = { 
            'conf': "/etc/ceph/ceph.conf" ,
            'filename': '/var/run/ceph/osd.{}-weight'.format(id),
            'timeout': 3600,
            'delay': 6
        }
        self.settings.update(kwargs)
        self.cluster=rados.Rados(conffile=self.settings['conf'])
        self.cluster.connect()

    def save(self):
        """
        Capture the current weight allowing the admin to undo simple mistakes.

        The weight file defaults to the /var/run directory and will not 
        survive a reboot.  
        """
        entry = self.osd_df()
        if 'crush_weight' in entry and entry['crush_weight'] != 0:
            with open(self.settings['filename'], 'w') as weightfile:
                weightfile.write("{}\n".format(entry['crush_weight']))


    def restore(self):
        """
        Set weight to previous setting
        """
        if os.path.isfile(self.settings['filename']):
            with open(self.settings['filename']) as weightfile:
                saved_weight = weightfile.read().rstrip('\n')
                log.info("Restoring weight {} to osd.{}".format(saved_weight, self.id))
                self.reweight(saved_weight)


    def reweight(self, weight):
        """
        Set the weight for the OSD
        Note: haven't found the equivalent api call for reweight
        """
        stdout = []
        stderr = []
        cmd = [ 'ceph', 'osd', 'crush', 'reweight', 'osd.{}'.format(self.id), weight ]
        proc = Popen(cmd, stdout=PIPE, stderr=PIPE)
        for line in proc.stdout:
            stdout.append(line.rstrip('\n'))
        for line in proc.stderr:
            stderr.append(line.rstrip('\n'))
        proc.wait()
        log.debug("Reweighting: {}".format(stderr))


    def osd_df(self):
        """
        Retrieve df entry for an osd
        """
        cmd = json.dumps({"prefix":"osd df", "format":"json" })
        ret,output,err = self.cluster.mon_command(cmd, b'', timeout=6)
        log.debug(json.dumps((json.loads(output)['nodes']), indent=4))
        for entry in json.loads(output)['nodes']:
            if entry['id'] == self.id:
                return entry
        log.warn("ID {} not found".format(self.id))
        return {}

    def wait(self):
        """
        Wait until PGs reach 0 or timeout expires
        """
        i = 0
        while i < self.settings['timeout']/self.settings['delay']:
            entry = self.osd_df()
            if 'pgs' in entry:
                if entry['pgs'] == 0:
                    log.info("osd.{} has no PGs".format(self.id))
                    return 
                else:
                    log.warn("osd.{} has {} PGs remaining".format(self.id, entry['pgs']))
            else:
                log.warn("osd.{} does not exist".format(self.id))
                return
            i += 1
            time.sleep(self.settings['delay'])

        log.debug("Timeout expired")
        raise RuntimeError("Timeout expired")

def zero_weight(id, **kwargs):
    """
    Set weight to zero and wait until PGs are moved
    """
    o = OSDWeight(id, **kwargs)
    o.save()
    o.reweight('0.0')
    o.wait()
    return True


def restore_weight(id, **kwargs):
    """
    Restore the previous setting for an OSD if possible
    """
    o = OSDWeight(id, **kwargs)
    o.restore()
    return True

