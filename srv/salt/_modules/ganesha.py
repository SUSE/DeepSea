# -*- coding: utf-8 -*-
"""
Ganesha configuration and exports
"""

from __future__ import absolute_import

import logging
from salt import client as SaltClient

try:
    from Ganesha.ganesha_mgr_utils import ExportMgr
except ImportError:
    ExportMgr = None

log = logging.getLogger(__name__)


def configurations():
    """
    Return the ganesha configurations.  The three answers are

    ganesha_configurations as defined in the pillar
    ganesha if defined
    [] for no ganesha
    """
    if 'roles' in __pillar__:
        if 'ganesha_configurations' in __pillar__:
            return list(set(__pillar__['ganesha_configurations']) &
                        set(__pillar__['roles']))
        if 'ganesha' in __pillar__['roles']:
            return ['ganesha']
    return []


def get_exports_info():
    """
    Returns the status info of each export exported by NFS-ganesha
    """
    caller = SaltClient.Caller()
    if not caller.cmd('service.status', 'nfs-ganesha'):
        return {'success': False, 'message': 'nfs-ganesha service is not running'}

    if not ExportMgr:
        return {'success': False, 'message': 'nfs-ganesha utils scripts are not installed'}

    mgr = ExportMgr('org.ganesha.nfsd', '/org/ganesha/nfsd/ExportMgr',
                    'org.ganesha.nfsd.exportmgr')
    status, msg, reply = mgr.ShowExports()
    if not status:
        return {'success': False, 'message': msg}

    exports = []
    for export in reply[1]:
        status2, msg2, reply2 = mgr.DisplayExport(export.ExportID)
        if not status2:
            exports.append({
                'export_id': export.ExportID,
                'path': export.ExportPath,
                'active': False,
                'message': msg2
            })
            continue

        exports.append({
            'export_id': export.ExportID,
            'path': reply2[1],
            'pseudo': reply2[2],
            'tag': reply2[3],
            'active': True
        })
    return {'success': True, 'exports': exports}
