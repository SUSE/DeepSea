#!/usr/bin/python

import os
import re
import pprint
from glob import glob
from subprocess import Popen, PIPE


def list():
    """
    Find all unpartitioned and allocated osds.  Return hwinfo dict.
    """
    drives = []
    for path in glob('/sys/block/*/device'):
        base = os.path.dirname(path)
        device = os.path.basename(base)
    
        # Skip partitioned, non-osd drives
        partitions = glob(base + "/" + device + "*")
        if partitions:
            for p in partitions:
                ids = [ re.sub('\D+', '', p) for p in partitions ]
            if not _osd("/dev/" + device, ids):
                continue
    
        # Skip removable media
        filename = base + "/removable"
        removable = open(filename).read().rstrip('\n')
        if (removable == "1"):
            continue
        filename = base + "/queue/rotational"
        rotational = open(filename).read().rstrip('\n')
        
        hardware =_hwinfo(device)
        hardware['device'] = device
        hardware['rotational'] = rotational

        drives.append(hardware)
    return drives
       
    
def _hwinfo(device):
    """
    Parse hwinfo output into dictionary
    """
    results = {}
    cmd = "/usr/sbin/hwinfo --disk --only /dev/{}".format(device)
    proc = Popen(cmd, stdout=PIPE, stderr=PIPE, shell=True)
    for line in proc.stdout:
        m = re.match("  ([^:]+): (.*)", line)
        if m:
            if (m.group(1) == "Capacity"):
                c = re.match("(\d+ \w+) \((\d+) bytes\)", m.group(2))
                if c:
                    results[m.group(1)] = c.group(1)
                    results['Bytes'] = c.group(2)
            else:
                results[m.group(1)] = re.sub(r'"', '', m.group(2))
    return results
    #for line in proc.stderr:
    #    print line

def _osd(device, ids):
    """
    Search for Ceph Data and Journal partitions
    """
    data = "Partition GUID code: 45B0969E-9B03-4F30-B4C6-B4B80CEFF106"
    journal = "Partition GUID code: 4FBD7E29-9D25-41B8-AFD0-062C0CEFF05D"
    for partition_id in ids:
        cmd = "/usr/sbin/sgdisk -i {} {}".format(partition_id, device)
        proc = Popen(cmd, stdout=PIPE, stderr=PIPE, shell=True)
        for line in proc.stdout:
            if (line.startswith(data) or line.startswith(journal)):
                return True
        for line in proc.stderr:
            print line
    return False
    

