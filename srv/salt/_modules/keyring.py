#!/usr/bin/python

import os
import struct
import base64
import time

def secret(filename):
    """
    """
    if os.path.exists(filename):
        with open(filename, 'r') as keyring:
            for line in keyring:
                if 'key' in line and ' = ' in line:
                    key = line.split(' = ')[1].strip()
                    return key

    key = os.urandom(16)
    header = struct.pack('<hiih',1,int(time.time()),0,len(key))
    return base64.b64encode(header + key)

