from salt.client import LocalClient
from ext_lib.utils import evaluate_state_return


def distribute():
    ret = LocalClient().cmd(
        "cluster:ceph",
        'state.apply', ['ceph.configuration'],
        tgt_type='pillar')
    return evaluate_state_return(ret)


def create():
    ret = LocalClient().cmd(
        "roles:master",
        'state.apply', ['ceph.configuration.create'],
        tgt_type='pillar')
    return evaluate_state_return(ret)


def deploy():
    """ Technically this is the wrong word.. Just keeping it consistent """
    if all([create(), distribute()]):
        return True
    return False
