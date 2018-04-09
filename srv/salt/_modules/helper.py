# -*- coding: utf-8 -*-
"""
Helper module to reuse Popen and byte->str casting
"""

# pylint: disable=incompatible-py3-code
import pprint

import logging
from subprocess import Popen, PIPE

log = logging.getLogger(__name__)


def convert_out(out):
    """
    Since python3 most system calls return type(byte)
    instead of type(str). We mostly use the output of
    those subprocess calls to make a decisions, which
    requires to manipulate and compare it.
    """
    if isinstance(out, bytes):
        return out.decode('ascii')
    elif isinstance(out, str):
        return out
    elif isinstance(out, int):
        return out
    elif isinstance(out, float):
        return out
    else:
        raise Exception("""Could not detect the type of {output}. Got {type_out}""".
                        format(output=out, type_out=type(out)))


def run(cmd, shell=False):
    """
    Generic function for running shell commands

    shell=False vs shell=True
    https://docs.python.org/2/library/subprocess.html#frequently-used-arguments
    We have some places in the code where we'd have to split the cmd's manually
    instead of relying on shlex.split or similar helpers.
    For now I'll place a destinction between pre-split commands that are processed
    on a per item level and entire strings that will be execcuted without extra
    pre-escaping and security measurements.
    """
    if isinstance(cmd, str):
        shell = True

    log.info("executing: {cmd}".format(cmd=cmd))
    proc = Popen(cmd, stdout=PIPE, stderr=PIPE, shell=shell)
    _stdout = convert_out(proc.stdout.read())
    _stdout = _stdout.rstrip()

    _stderr = convert_out(proc.stdout.read())
    _stderr = _stderr.rstrip()

    _retcode = proc.wait()
    log.debug("returncode of {cmd}: {rc}".format(cmd=cmd, rc=_retcode))

    log.debug("""stdout of {cmd}:
{out}""".format(cmd=cmd, out=pprint.pformat(_stdout)))
    log.debug("""stderr of {cmd}:
{out}""".format(cmd=cmd, out=pprint.pformat(_stderr)))
    return _retcode, _stdout, _stderr
