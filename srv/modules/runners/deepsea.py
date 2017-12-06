# -*- coding: utf-8 -*-
"""
This runner implements helper functions for DeepSea in general
"""

from __future__ import absolute_import

import re


def version(**kwargs):
    # pylint: disable=W0613
    """
    Returns the DeepSea version info currently installed
    """
    ver = "@VERSION@"
    match = re.match(r'^([\d\.]+)(\+git\.(\d+).(\w+))?', ver)
    if match:
        return {
            'full_version': ver,
            'version': match.group(1),
            'git_offset': match.group(3),
            'git_hash': match.group(4)
        }
    return {
        'full_version': None,
        'version': None,
        'git_offset': None,
        'git_hash': None
    }
