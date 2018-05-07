# -*- coding: utf-8 -*-
# pylint: disable=modernize-parse-error
"""
Settings Helper class to export the __opts__ dunder.
"""

from __future__ import absolute_import
import salt.config


# pylint: disable=too-few-public-methods
class Settings(object):
    """
    Common settings
    """
    def __init__(self):
        """
        Assign root_dir, salt __opts__ and stack configuration.  (Stack
        configuration is not used currently.)
        """
        __opts__ = salt.config.client_config('/etc/salt/master')
        self.__opts__ = __opts__

        for ext in __opts__['ext_pillar']:
            if 'stack' in ext:
                self.stack = ext['stack']
        self.root_dir = "/srv/pillar/ceph/proposals"


def self_():
    """
    Salt exporter func
    """
    return Settings()
