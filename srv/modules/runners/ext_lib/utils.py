from salt.client import LocalClient
from salt.runner import RunnerClient
from salt.config import client_config
from salt.loader import utils, minion_mods
from .validator import evaluate_module_return, evaluate_state_return
from .exceptions import ModuleException, RunnerException
import logging

ROLE_CEPH_MON = 'mon'


def master_minion():
    '''
    Load the master modules
    '''
    __master_opts__ = client_config("/etc/salt/master")
    __master_utils__ = utils(__master_opts__)
    __salt_master__ = minion_mods(__master_opts__, utils=__master_utils__)
    return __salt_master__["master.minion"]()


log = logging.getLogger(__name__)


def runner(opts=None):
    """ TODO: docstring """
    log.debug("Initializing runner")
    runner = RunnerClient(opts)
    __master_opts__ = client_config("/etc/salt/master")
    __master_opts__['quiet'] = True
    qrunner = RunnerClient(__master_opts__)
    return qrunner


def cluster_minions():
    """ Technically this should come from select.py

    TODO:
    Move select.py in this realm (/ext_lib) and make it python-import consumable
    """
    log.debug("Searching for cluster_minions")
    # client = salt.client.get_local_client(__opts__['conf_file'])
    potentials = LocalClient().cmd(
        "I@deepsea_minions:*", 'test.true', tgt_type='compound')
    minions = list()
    for k, v in potentials.items():
        if v:
            minions.append(k)
    return minions


def prompt(message,
           options='(y/n)',
           non_interactive=False,
           default_answer=False):
    """ TODO: docstring """
    if non_interactive:
        log.debug(
            f"running in non-interactive mode. default answer is {default_answer}"
        )
        return default_answer
    answer = input(f"{message} - {options}")
    if answer.lower() == 'y' or answer.lower() == 'Y':
        return True
    elif answer.lower() == 'n' or answer.lower() == 'N':
        return False
    else:
        answer = input(f"You typed {answer}. We accept {options}")
        prompt(message, options=options)


def _get_candidates(role=None):
    """ TODO: docstring """

    # Is this the right appracoh or should cephprocesses be used again?
    # TODO: This needs to be improved

    assert role
    all_minions = LocalClient().cmd(
        f"roles:{role}", f'{role}.already_running', tgt_type='pillar')

    candidates = list()

    for k, v in all_minions.items():
        if not v:
            candidates.append(k)
    return candidates


def _is_running(role_name=None, minion=None, func='wait_role_up'):
    """ TODO: docstring """
    assert role_name
    search = f"I@role:{role_name}"
    running = True
    if minion:
        search = minion
    print("Checking if processes are running. This may take a while..")
    minions_return = LocalClient().cmd(
        search,
        f'cephprocesses.{func}', [f"role={role_name}"],
        tgt_type='compound')
    for minion, status in minions_return.items():
        # TODO: Refactor the 'wait_role_down' function. This is horrible
        if status:
            print(f"role-{role_name} is running on {minion}")
            print(
                f"This is showing the wrong status for role deletion currently"
            )
        if not status:
            print(
                f"This is showing the wrong status for role deletion currently"
            )
            print(f"role-{role_name} is *NOT* running on {minion}")
            running = False
    return running


def _distribute_file(file_name='',
                     dest='',
                     candidate='',
                     target_name='keyring'):
    """ TODO docstring """
    assert candidate
    assert file_name
    assert dest

    ensure_permissions()

    print(f"Distributing file: {file_name} to {candidate}")

    # TODO: be more specific in debug logging

    ret: str = LocalClient().cmd(
        candidate, 'file.mkdir', [dest], tgt_type='glob')
    if not evaluate_module_return(ret, context=f'file.mkdir {dest}'):
        return False

    ret: str = LocalClient().cmd(
        candidate,
        'cp.get_file',
        [f'salt://ceph/bootstrap/{file_name}', f'{dest}/{target_name}'],
        tgt_type='glob')

    # TODO: Improve evaluate_module_return func
    if not evaluate_module_return(
            ret, context=f'cp.get_file {file_name} to {dest}'):
        return False
    return True


def ensure_permissions():
    # TODO: do I need to have that in a state?

    # TODO: there is file.chown .. replace it with that
    # TODO: also there is fole.access which may need to used before
    ret: str = LocalClient().cmd(
        'roles:master', 'state.apply', ['ceph.permissions'], tgt_type='pillar')
    if not evaluate_state_return(ret):
        return False


def _distribute_bootstrap_items(hostname):
    """ TODO docstring """
    # TODO: evaluate returns
    print("Copying bootstrap items to respective minions..")

    ensure_permissions()

    # TODO replace /var/lib/ceph/tmp with pillar variable
    # TODO: Improve evaluate_module_return func

    print(f"Distributing the bootstrap admin keyring to {hostname}")
    ret: str = LocalClient().cmd(
        hostname,
        'cp.get_file', ['salt://ceph/bootstrap/keyring', '/var/lib/ceph/tmp/'],
        tgt_type='glob')
    if not evaluate_module_return(ret, context='cp.get_file keyring'):
        return False

    ret: str = LocalClient().cmd(
        hostname,
        'cp.get_file',
        ['salt://ceph/bootstrap/ceph.keyring', '/var/lib/ceph/tmp/'],
        tgt_type='glob')
    if not evaluate_module_return(ret, context='cp.get_file ceph.keyring'):
        return False

    print("Distributing the admin keyring to the admin nodes")
    ret: str = LocalClient().cmd(
        # also distribute the admin keyring on role:admin role:master and role:mon
        # TODO: also on role mon? actually not..o
        'roles:admin',
        'cp.get_file',
        ['salt://ceph/bootstrap/ceph.client.admin.keyring', '/etc/ceph/'],
        tgt_type='pillar')
    if not evaluate_module_return(ret, context='cp.get_file admin.keyring'):
        return False

    print("Distributing the admin keyring to the master node")
    ret: str = LocalClient().cmd(
        # also distribute the admin keyring on role:admin role:master and role:mon
        'roles:master',
        'cp.get_file',
        ['salt://ceph/bootstrap/ceph.client.admin.keyring', '/etc/ceph/'],
        tgt_type='pillar')
    if not evaluate_module_return(ret, context='cp.get_file admin.keyring'):
        return False


def is_running(minion, role_name=None, func='wait_role_up'):
    assert role_name
    if _is_running(role_name=role_name, minion=minion, func=func):
        return True
    return False


def humanize_return(inp):
    if inp:
        return 'success'
    return 'failure'


def exec_runner(cmd, cmd_args=[], failhard=True):
    # This must always include `machine=True` to get
    # a tuple as return
    cmd_args.append('called_by_runner=True')

    ret = runner().cmd(cmd, cmd_args)
    if isinstance(ret, list):
        # we get a list of return values back [True, True]
        # pretty useless at that point..
        return ret
    if isinstance(ret, str):
        # We may be a bit more specific and search for *which* Exception was raised.
        if ret.startswith('Exception occurred in runner'):
            if failhard:
                raise RunnerException(cmd)
            # TODO:
            # What to do in the failhard=False case?
            pass
    #TODO else
