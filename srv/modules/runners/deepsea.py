# -*- coding: utf-8 -*-
"""
This runner implements helper functions for DeepSea in general
"""

DEEPSEA_VERSION = 'DEVVERSION'


def version(**kwargs):
    # pylint: disable=unused-argument
    """
    Returns the DeepSea version info currently installed
    """
    return DEEPSEA_VERSION
