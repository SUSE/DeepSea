# -*- coding: utf-8 -*-
"""
This module provides helper classes to call salt
"""
from __future__ import absolute_import

import salt.client
import salt.minion


class SaltClient(object):
    _OPTS_ = None
    _CALLER_ = None
    _LOCAL_ = None
    _MASTER_ = None

    @classmethod
    def _opts(cls):
        """
        Initializes and retrieves the Salt opts structure
        """
        if cls._OPTS_ is None:
            cls._OPTS_ = salt.config.minion_config('/etc/salt/minion')
        return cls._OPTS_

    @classmethod
    def caller(cls):
        """
        Initializes and retrieves the Salt caller client instance
        """
        if cls._CALLER_ is None:
            cls._CALLER_ = salt.client.Caller(mopts=cls._opts())
        return cls._CALLER_

    @classmethod
    def local(cls):
        """
        Initializes and retrieves the Salt local client instance
        """
        if cls._LOCAL_ is None:
            cls._LOCAL_ = salt.client.LocalClient()
        return cls._LOCAL_

    @classmethod
    def master(cls):
        if cls._MASTER_ is None:
            _opts = salt.config.master_config('/etc/salt/master')
            _opts['file_client'] = 'local'
            cls._MASTER_ = salt.minion.MasterMinion(_opts)
        return cls._MASTER_

    @classmethod
    def pillar_fs_path(cls):
        return cls.master().opts['pillar_roots']['base'][0]
