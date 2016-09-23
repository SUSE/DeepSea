#!/usr/bin/python

import os
import struct
import base64
import time

def secret():
    """
    """
    key = os.urandom(16)
    header = struct.pack('<hiih',1,int(time.time()),0,len(key))
    return base64.b64encode(header + key)

