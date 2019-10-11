# -*- coding: utf-8 -*-
"""
The need for this module is that the roles show the intended state and not
the current state.  Once the admin unassigns the monitor role, the pillar
reflects that configuration.
"""

from __future__ import absolute_import
import logging
# pylint: disable=import-error,3rd-party-module-not-gated
from subprocess import check_output, CalledProcessError
log = logging.getLogger(__name__)
from salt.exceptions import CommandExecutionError
from ext_lib.utils import _run_cmd


########################## THIS IS JUST FOR SHOWCASING THE DIFFERENT SOLUTIONS TO REMOTE EXECUTION ######################

def already_running():
    # check if a container is already running.
    # Check the higher-level instance - systemd.

    ## there needs to be a second check for existence..
    ## we might have the case where a mon is down, but still exists
    ## check for directory existence? or for podman image existance?

    # TODO: refine the logic when to return false/true..

    # is /host/ fine?
    mon_name = __grains__.get('host', '')
    if not mon_name:
        log.error("Could not retrieve host grain. Aborting")
        return False
    try:
        status = check_output(
            ['systemctl', 'is-active',
             f'ceph-mon@{mon_name}.service']).decode('utf-8').strip()
    except CalledProcessError as e:
        log.info(f'{e}')
        return False
    if status == 'active':
        return True
    elif status == 'inactive' or os.path.exists(
            f'/var/lib/ceph/mon/ceph-{mon_name}'):
        return False
    else:
        log.error(f"Could not determine state of {mon_name}")
        return False


def deploy_salt_run():
    try:
        ret = __salt__['cmd.run_all']('lsa')
    except CommandExecutionError as e:
        """
        e exposes:
        ['error', 'info', 'strerror_without_changes', 'message', 'strerror', '__module__', '__doc__', '__init__', '__unicode__', 'pack', '__weakref__', '__new__', '__repr__', '__str__', '__getattribute__', '__setattr__', '__delattr__', '__reduce__', '__setstate__', 'with_traceback', '__suppress_context__', '__dict__', 'args', '__traceback__', '__context__', '__cause__', '__hash__', '__lt__', '__le__', '__eq__', '__ne__', '__gt__', '__ge__', '__reduce_ex__', '__subclasshook__', '__init_subclass__', '__format__', '__sizeof__', '__dir__', '__class__']
        All of the interesting fields like 'error', 'info', 'message', 'strerror' include
        the same message of type(str)

        "Unable to run command '['lsa']' with the context '{'cwd': '/root', 'shell': False, 'env': {'LS_COLORS': 'no=00:fi=00:di=01;34:ln=00;36:pi=40;33:so=01;35:do=01;35:bd=40;33;01:cd=40;33;01:or=41;33;01:ex=00;32:*.cmd=00;32:*.exe=01;32:*.com=01;32:*.bat=01;32:*.btm=01;32:*.dll=01;32:*.tar=00;31:*.tbz=00;31:*.tgz=00;31:*.rpm=00;31:*.deb=00;31:*.arj=00;31:*.taz=00;31:*.lzh=00;31:*.lzma=00;31:*.zip=00;31:*.zoo=00;31:*.z=00;31:*.Z=00;31:*.gz=00;31:*.bz2=00;31:*.tb2=00;31:*.tz2=00;31:*.tbz2=00;31:*.xz=00;31:*.avi=01;35:*.bmp=01;35:*.dl=01;35:*.fli=01;35:*.gif=01;35:*.gl=01;35:*.jpg=01;35:*.jpeg=01;35:*.mkv=01;35:*.mng=01;35:*.mov=01;35:*.mp4=01;35:*.mpg=01;35:*.pcx=01;35:*.pbm=01;35:*.pgm=01;35:*.png=01;35:*.ppm=01;35:*.svg=01;35:*.tga=01;35:*.tif=01;35:*.webm=01;35:*.webp=01;35:*.wmv=01;35:*.xbm=01;35:*.xcf=01;35:*.xpm=01;35:*.aiff=00;32:*.ape=00;32:*.au=00;32:*.flac=00;32:*.m4a=00;32:*.mid=00;32:*.mp3=00;32:*.mpc=00;32:*.ogg=00;32:*.voc=00;32:*.wav=00;32:*.wma=00;32:*.wv=00;32:', 'HOSTTYPE': 'x86_64', 'LESSCLOSE': 'lessclose.sh %s %s', 'XKEYSYMDB': '/usr/X11R6/lib/X11/XKeysymDB', 'LANG': 'POSIX', 'WINDOWMANAGER': 'xterm', 'LESS': '-M -I -R', 'SUDO_GID': '1000', 'HOSTNAME': 'admin', 'CSHEDIT': 'emacs', 'GPG_TTY': '/dev/pts/0', 'LESS_ADVANCED_PREPROCESSOR': 'no', 'COLORTERM': '1', 'USERNAME': 'root', 'SUDO_COMMAND': '/bin/bash', 'MACHTYPE': 'x86_64-suse-linux', 'MINICOM': '-c on', 'OSTYPE': 'linux', 'USER': 'root', 'PAGER': 'less', 'MORE': '-sl', 'PWD': '/root', 'HOME': '/root', 'LC_CTYPE': 'C', 'HOST': 'admin', 'SUDO_USER': 'vagrant', 'XNLSPATH': '/usr/X11R6/lib/X11/nls', 'XDG_DATA_DIRS': '/usr/share', 'PROFILEREAD': 'true', 'SUDO_UID': '1000', 'MAIL': '/var/mail/root', 'LESSKEY': '/etc/lesskey.bin', 'SHELL': '/bin/bash', 'TERM': 'screen-256color', 'LS_OPTIONS': '-A -N --color=tty -T 0', 'SHLVL': '1', 'MANPATH': '/usr/share/man:/usr/local/man', 'LOGNAME': 'root', 'XDG_CONFIG_DIRS': '/etc/xdg', 'PATH': '/sbin:/usr/sbin:/usr/local/sbin:/root/bin:/usr/local/bin:/usr/bin:/bin', 'G_BROKEN_FILENAMES': '1', 'HISTSIZE': '1000', 'CPU': 'x86_64', 'LESSOPEN': 'lessopen.sh %s', '_': '/usr/bin/salt-call', 'LC_NUMERIC': 'C', 'LC_TIME': 'C', 'LC_COLLATE': 'C', 'LC_MONETARY': 'C', 'LC_MESSAGES': 'C', 'LC_PAPER': 'C', 'LC_NAME': 'C', 'LC_ADDRESS': 'C', 'LC_TELEPHONE': 'C', 'LC_MEASUREMENT': 'C', 'LC_IDENTIFICATION': 'C', 'LANGUAGE': 'C'}, 'stdin': None, 'stdout': -1, 'stderr': -1, 'with_communicate': True, 'timeout': None, 'bg': False, 'close_fds': True}', reason: [Errno 2] No such file or directory: 'lsa': 'lsa': lsa"

        Which makes it really hard to extract the ['reason'] of 'No such file or directory'

        stdout and stderr and also populated with -1 and -1, which is not terribly helpful.
        Also the output is filled with unrelated stuff..

        On the plus side we only have to worry about one type of exception (I guess?)
        This is probably good and bad at the same time. We loose the ability to react
        based on the exceptions we see. On the other hand we don't have to care as much.

        Does this sound like catching bare Exceptions?

        """
        print(e)

    try:
        ret = __salt__['cmd.run_all']('echo foobar')
    except CommandExecutionError as e:
        print(e)
    print(ret)

def deploy_popen_run():
    ret = _run_cmd(['lsa'], func_name='deploy_popen_run', module_name='mon')
    print(ret.__dict__)

    """
    Is centrally handled inside _run_cmd
    (raises FileNotFoundError)

    exposes:
    ['__init__', '__doc__', '__str__', '__new__', '__reduce__', 'errno', 'strerror', 'filename', 'filename2', 'characters_written', '__repr__', '__getattribute__', '__setattr__', '__delattr__', '__setstate__', 'with_traceback', '__suppress_context__', '__dict__', 'args', '__traceback__', '__context__', '__cause__', '__hash__', '__lt__', '__le__', '__eq__', '__ne__', '__gt__', '__ge__', '__reduce_ex__', '__subclasshook__', '__init_subclass__', '__format__', '__sizeof__', '__dir__', '__class__']

    The attributes return what they're expected to:

    e.errno -> 2
    e.strerror -> "No such file or directory: 'lsa'"
    e.filename -> 'lsa'

    also it's missing the 'command', 'args' field :/

    Certainly it's not ideal that this Exception doesn't follow *a* convention, but that's what we have the
    class for.
    """

    ret = _run_cmd('echo foobar', func_name='deploy_popen_run', module_name='mon')
    print(ret.__dict__)


def deploy_failed():
    # image_name = whatever comes from #ceph config get mon container_image foo  or from salt
    image_name = 'foo' # retrieve the image here to be able to have different versions for mons than for other daemons
    hostname = 'my_hostname' # from salt
    fsid = 'foo' # fsid either get from ceph config get mgr.1 fsid or from salt
    mon_ip = '0.0.0.0.0' # from salt
    keyring_path = 'foo' # This is a prerequisite. (maybe passed as an argument from the runner? Limits the debugging ease)
    config_path = 'foo' # This is a prerequisite.

    cmd = f'ceph-daemon --image {image_name} deploy --name mon mon.{hostname} --fsid {fsid} --mon-ip {mon_ip}, --keyring {keyring_path} --config {config_path}'

    ret = _run_cmd(cmd, func_name='deploy_dummy', module_name='mon', hostname=hostname)
    return ret.__dict__

def deploy_success():
    # image_name = whatever comes from #ceph config get mon container_image foo  or from salt
    image_name = 'foo' # retrieve the image here to be able to have different versions for mons than for other daemons
    hostname = 'my_hostname' # from salt
    fsid = 'foo' # fsid either get from ceph config get mgr.1 fsid or from salt
    mon_ip = '0.0.0.0.0' # from salt
    keyring_path = 'foo' # This is a prerequisite. (maybe passed as an argument from the runner? Limits the debugging ease)
    config_path = 'foo' # This is a prerequisite.

    cmd = f'echo --image {image_name} deploy --name mon mon.{hostname} --fsid {fsid} --mon-ip {mon_ip}, --keyring {keyring_path} --config {config_path}'

    ret = _run_cmd(cmd, func_name='deploy_dummy', module_name='mon', hostname=hostname)
    return ret.__dict__

########################## THIS IS JUST FOR SHOWCASING THE DIFFERENT SOLUTIONS TO REMOTE EXECUTION ######################
