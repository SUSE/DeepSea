# -*- coding: utf-8 -*-
import logging
import json

from salt.exceptions import CommandExecutionError

log = logging.getLogger(__name__)


def returnstruct(name, command=None):
    '''
    Set default values for return structure
    '''
    ret = {
        'name': name,
        'command': command,
        'stdout': '',
        'stderr': '',
        'result': False,
        'timeout': 0,
        'comment': ''
    }
    return ret


def outputter(ret, out, opts):
    '''
    Reformat structure as string for human interaction.  Provide any stdout,
    stderr and comment. If all are absent, return Success.  On failure, return
    command and retcode as well.

    If out is specified, return the data in that format.
    '''
    if 'output' in opts:
        out = "raw"  # prevent double processing

    if out == None:
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
                   f"returned {ret['retcode']}\n"
                   f"{ret['stdout']}\n"
                   f"{ret['stderr']}\n"
                   f"\n{ret['comment']}\n")
            return msg + "Failure"
    elif out == "yaml":
        return ret
    elif out == "raw":
        return ret
    elif out == "json":
        return json.dumps(ret, indent=4)
    else:
        raise CommandExecutionError(f"output type {out} unsupported")
        return __salt__['out.out_format'](ret, out=out)
