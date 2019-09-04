from salt.client import LocalClient
from salt.runner import RunnerClient
from salt.config import client_config
from salt.loader import utils, minion_mods
from subprocess import check_output
import logging


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
    __master_opts__['quiet'] = False
    qrunner = RunnerClient(__master_opts__)
    return qrunner


def cluster_minions():
    """ Technically this should come from select.py

    TODO:
    Move select.py in this realm (/ext_lib) and make it python-import consumable
    """
    log.debug("Searching for cluster_minions")
    potentials = LocalClient().cmd(
        "I@deepsea_minions:*", 'test.ping', tgt_type='compound')
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


def evaluate_module_return(job_data, context=''):
    failed = False
    for minion_id, result in job_data.items():
        log.debug(f"results for job on minion: {minion_id} is: {result}")
        if not result:
            print(
                f"Module call failed on {minion_id} with {result if result else 'n/a'} and context: {context}"
            )
            failed = True

    if failed:
        return False
    return True


def evaluate_state_return(job_data):
    """ TODO """
    # does log.x actually log in the salt log? I don't think so..
    failed = False
    for minion_id, job_data in job_data.items():
        log.debug(f"{job_data} ran on {minion_id}")
        if isinstance(job_data, list):
            # if a _STATE_ is not available, salt returns a list with an error in idx0
            # thanks salt for staying consistent..
            log_n_print(job_data)
            return False
        if isinstance(job_data, str):
            # In this case, it's a _MODULE_ that salt can't find..
            # again, thanks salt for staying consistent..
            log_n_print(job_data)
            return False

        for jid, metadata in job_data.items():
            log.debug(f"Job {jid} run under: {metadata.get('name', 'n/a')}")
            log.debug(
                f"Job {jid } was successful: {metadata.get('result', False)}")
            if not metadata.get('result', False):
                log.debug(
                    f"Job {metadata.get('name', 'n/a')} failed on minion: {minion_id}"
                )
                print(
                    f"Job {metadata.get('name', 'n/a')} failed on minion: {minion_id}"
                )
                failed = True
    if failed:
        return False
    return True


def log_n_print(message):
    """ TODO: docstring """
    # TODO: I assume I have to pass a context logger to this function when invoked from a salt_module
    # this lib is not executed with the salt context, hence no logging will end up in the salt-master logs
    log.debug(message)
    print(message)


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
    log_n_print("Checking if processes are running. This may take a while..")
    minions_return = LocalClient().cmd(
        search,
        f'cephprocesses.{func}', [f"role={role_name}"],
        tgt_type='compound')
    for minion, status in minions_return.items():
        # TODO: Refactor the 'wait_role_down' function. This is horrible
        if status:
            log_n_print(f"role-{role_name} is running on {minion}")
            log_n_print(
                f"This is showing the wrong status for role deletion currently"
            )
        if not status:
            log_n_print(
                f"This is showing the wrong status for role deletion currently"
            )
            log_n_print(f"role-{role_name} is *NOT* running on {minion}")
            running = False
    return running


def _remove_role(role=None, non_interactive=False):
    # TODO: already_running vs is_running
    # find process id vs. systemd
    ##
    ## There is mon ok-to-rm, ok-to-stop, ok-to-add-offline
    ##
    """ TODO: docstring """
    assert role
    already_running = LocalClient().cmd(
        f"not I@roles:{role}", f'{role}.already_running', tgt_type='compound')
    to_remove = [k for (k, v) in already_running.items() if v]
    if not to_remove:
        print("Nothing to remove. Exiting..")
        return True
    if prompt(
            f"""Removing role: {role} on minion {', '.join(to_remove)}
Continue?""",
            non_interactive=non_interactive,
            default_answer=True):
        print(f"Removing {role} on {' '.join(to_remove)}")
        ret: str = LocalClient().cmd(
            to_remove,
            f'podman.remove_{role}',
            ['registry.suse.de/devel/storage/6.0/images/ses/6/ceph/ceph'],
            tgt_type='list')
        if not evaluate_module_return(ret):
            return False

        ret = [
            is_running(minion, role_name=role, func='wait_role_down')
            for minion in to_remove
        ]
        # TODO: do proper checks here:
        if all(ret):
            print(f"{role} deletion was successful.")
            return True
        return False

    else:
        return 'aborted'


def _create_bootstrap_items():
    """ TODO docstring """
    log_n_print("Creating bootstrap items..")
    ret: str = LocalClient().cmd(
        'roles:master', 'podman.create_bootstrap_items', tgt_type='pillar')
    if not evaluate_module_return(ret):
        return False


def _create_initial_monmap(hostname):
    """ TODO docstring """
    log_n_print("Creating bootstrap items..")
    ret: str = LocalClient().cmd(
        hostname, 'podman.create_initial_monmap', tgt_type='glob')
    if not evaluate_module_return(ret):
        return False
    return ret


def _create_mgr_keyring(hostname):
    """ TODO docstring """
    log_n_print("Creating mgr keyring..")
    ret: str = LocalClient().cmd(
        'roles:master',
        'podman.create_mgr_keyring', [hostname],
        tgt_type='pillar')

    if not evaluate_module_return(ret):
        return False
    return ret


def _create_mon_keyring(name):
    """ TODO docstring """

    # TODO: refactor keyring methods, can be only once with parameters

    log_n_print("Creating mon keyring..")
    ret: str = LocalClient().cmd(
        'roles:master', 'podman.create_mon_keyring', [name], tgt_type='pillar')

    if not evaluate_module_return(ret):
        return False
    return ret


def _get_monmap(name):
    """ TODO docstring """

    log_n_print(f"Retrieving monmap for {name}..")
    ret: str = LocalClient().cmd(
        'roles:master', 'podman.get_monmap', [name], tgt_type='pillar')

    if not evaluate_module_return(ret):
        return False
    return ret


def _distribute_file(file_name='',
                     dest='',
                     candidate='',
                     target_name='keyring'):
    """ TODO docstring """
    assert candidate
    assert file_name
    assert dest

    ensure_permissions()
    ensure_dirs_exist()

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


def ensure_dirs_exist():
    ret: str = LocalClient().cmd(
        # TODO: 1) don't rely on podman to create dirs
        # TODO: 2) Change targeting from * to individual roles
        '*',
        'podman.ensure_dirs_exist',
        tgt_type='glob')
    if not evaluate_module_return(ret, context='ensure_dirs_exist'):
        return False


def ensure_permissions():
    # TODO: do I need to have that in a state?
    ret: str = LocalClient().cmd(
        'roles:master', 'state.apply', ['ceph.permissions'], tgt_type='pillar')
    if not evaluate_state_return(ret):
        return False


def _distribute_bootstrap_items(hostname):
    """ TODO docstring """
    # TODO: evaluate returns
    log_n_print("Copying bootstrap items to respective minions..")

    ensure_permissions()
    ensure_dirs_exist()

    # TODO replace /var/lib/ceph/tmp with pillar variable
    # TODO: Improve evaluate_module_return func

    log_n_print(f"Distributing the bootstrap admin keyring to {hostname}")
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

    log_n_print("Distributing the admin keyring to the admin nodes")
    ret: str = LocalClient().cmd(
        # also distribute the admin keyring on role:admin role:master and role:mon
        # TODO: also on role mon? actually not..o
        'roles:admin',
        'cp.get_file',
        ['salt://ceph/bootstrap/ceph.client.admin.keyring', '/etc/ceph/'],
        tgt_type='pillar')
    if not evaluate_module_return(ret, context='cp.get_file admin.keyring'):
        return False

    log_n_print("Distributing the admin keyring to the master node")
    ret: str = LocalClient().cmd(
        # also distribute the admin keyring on role:admin role:master and role:mon
        'roles:master',
        'cp.get_file',
        ['salt://ceph/bootstrap/ceph.client.admin.keyring', '/etc/ceph/'],
        tgt_type='pillar')
    if not evaluate_module_return(ret, context='cp.get_file admin.keyring'):
        return False


def _deploy_role(role=None, candidates=[], non_interactive=False):
    assert role
    if not candidates:
        print(f"No candidates for a {role} deployment found")
        return True

    if not prompt(
            f"""These minions will be {role}s: {', '.join(candidates)}
Continue?""",
            non_interactive=non_interactive,
            default_answer=True):
        print("Aborted..")
        return False

    print("Deploying..")
    ret: str = LocalClient().cmd(
        candidates, f'podman.create_{role}', tgt_type='list')

    if not evaluate_module_return(ret):
        return False

    # TODO: query in a loop with a timeout
    # TODO: Isn't that what we have in cephproceses.wait?
    # TODO: Check that.
    ret = [is_running(minion, role_name=role) for minion in candidates]
    if not all(ret):
        print(f"{role} deployment was not successful.")
        return False
    return True


def is_running(minion, role_name=None, func='wait_role_up'):
    assert role_name
    if _is_running(role_name=role_name, minion=minion, func=func):
        return True
    return False


def run_and_eval(runner_name, extra_args=None, opts={}):
    # TODO: maybe supress the 'True' output from the screen
    qrunner = runner(opts)
    if not qrunner.cmd(runner_name, extra_args):
        log_n_print(f"{runner_name} failed.")
        raise Exception()


def _read_policy_cfg():
    policy_path = LocalClient().cmd("", 'test.ping', tgt_type='compound')
    with open(policy_path, 'r') as _fd:
        return _fd.read()


def _query_master_pillar(key=None):
    assert key
    ret = LocalClient().cmd(
        "roles:master", 'pillar.get', [key], tgt_type='pillar')
    values = list(ret.values())
    if not values:
        # TODO: really false?
        return False
    return values[0]
