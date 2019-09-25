# -*- coding: utf-8 -*-
import logging
import json


log = logging.getLogger(__name__)


def err(ret, msg):
    '''
    Set the comment field, log the error message and return
    '''
    ret['comment'] = msg
    log.error(msg)
    return ret


def returnstruct(name):
    '''
    Set default values for return structure
    '''
    ret = {
        'name': name,
        'command': '',
        'stdout': '',
        'stderr': '',
        'result': False,
        'returncode': '',
        'timeout': 0,
        'comment': ''
    }
    return ret


def outputter(ret, out_type):
    '''
    Reformat structure as string for human interaction.  Provide any stdout,
    stderr and comment. If all are absent, return Success.  On failure, return
    command and returncode as well.

    If out_type is specified, return the data in that format.
    '''
    if out_type == None:
        # Unstructured
        if ret['result']:
            msg = ""
            if ret['stdout']:
                msg += f"{ret['stdout']}\n"
            if ret['stderr']:
                msg += f"{ret['stderr']}\n"
            if ret['comment']:
                msg += f"\n{ret['comment']}"

            if msg:
                return msg
            return "Success"
        else:
            msg = (f"{ret['command']}\n"
                   f"returned {ret['returncode']}\n"
                   f"{ret['stdout']}\n"
                   f"{ret['stderr']}\n"
                   f"\n{ret['comment']}\n")
            return msg + "Failure"
    elif out_type == "yaml":
        return ret
    elif out_type == "raw":
        return ret
    elif out_type == "json":
        return json.dumps(ret, indent=4)
    else:
        return __salt__['out.out_format'](ret, out=out_type)
