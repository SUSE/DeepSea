# -*- coding: utf-8 -*-
"""
This runner implements helper functions for DeepSea in general
"""

from __future__ import absolute_import
import re

DEEPSEA_VERSION = '0.0.0'


# pylint: disable=redefined-builtin
def version(**kwargs):
    """
    Returns the DeepSea version info currently installed
    """
    format_ = kwargs['format'] if 'format' in kwargs else 'plain'

    if format_ == 'json':
        try:
            ver = re.search(r'(^\d+(\.\d+)+)', DEEPSEA_VERSION).group(0)
        except AttributeError:
            ver = '0.0.0'
        offset = re.findall(r'\+\d+', DEEPSEA_VERSION)
        hash_ = re.findall(r'[\w]{7,8}$', DEEPSEA_VERSION)

        return {'full_version': DEEPSEA_VERSION,
                'version': ver,
                'git_offset': offset[0].lstrip('+') if offset else '0',
                'git_hash': hash_[0][-7:] if hash_ else ''}

    return DEEPSEA_VERSION
