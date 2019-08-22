from salt.client import LocalClient
from salt.runner import RunnerClient
from salt.config import client_config
import logging

log = logging.getLogger(__name__)


def runner(opts):
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
        "I@cluster:ceph", 'test.ping', tgt_type='compound')
    minions = list()
    for k, v in potentials.items():
        if v:
            minions.append(k)
    return minions


def prompt(message,
           options='(y/n)',
           non_interactive=False,
           default_answer=False):
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


def evaluate_module_return(job_data):
    failed = False
    for minion_id, result in job_data.items():
        log.debug(f"results for job are: {result} - running on {minion_id}")
        if not result:
            print(f"Module call failed on {minion_id}")
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
    log.debug(message)
    print(message)
