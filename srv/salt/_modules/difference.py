# -*- coding: utf-8 -*-
"""
Jinja in Salt 2016.11.4 is missing the difference function.

This Salt module is for the benefit of those attempting to debug from the command line.  Any orchestrations call the Salt master module located in /srv/modules/modules and not this one.  SES5 is reaching EOL and while this is technically not needed, it may help other maintainers.
"""

import logging

log = logging.getLogger(__name__)


def of_(*args):
    """
    Remove all remaining lists from the first
    """
    start = set(args[0])
    log.debug("start: {}".format(start))
    for arg in args[1:]:
        log.debug("remove {}".format(arg))
        start -= set(arg)
    log.debug("finally: {}".format(start))
    return list(start)

__func_alias__ = {
                'of_': 'of',
}

