from salt.client import LocalClient
from salt.runner import RunnerClient
from salt.config import client_config

def runner(opts):
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
    potentials = LocalClient().cmd("I@cluster:ceph", 'test.ping', tgt_type='compound')
    minions = list()
    for k, v in potentials.items():
        if v:
            minions.append(k)
    return minions
