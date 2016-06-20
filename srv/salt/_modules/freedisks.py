#!/usr/bin/python

import os
import re
import pprint
from glob import glob
from subprocess import Popen, PIPE


def list():
    """
    """
    drives = []
    for path in glob('/sys/block/*/device'):
        base = os.path.dirname(path)
        device = os.path.basename(base)
    
        # Skip partitioned drives
        partitions = glob(base + "/" + device + "*")
        if partitions:
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

