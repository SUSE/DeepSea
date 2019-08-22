from salt.client import LocalClient


def distribute_ceph_conf():
    LocalClient().cmd(
        "cluster:ceph",
        'state.apply', ['ceph.configuration'],
        tgt_type='pillar')
    return True


def create_ceph_conf():
    LocalClient().cmd(
        "roles:master",
        'state.apply', ['ceph.configuration.create'],
        tgt_type='pillar')


def create_and_distribute_ceph_conf():
    create_ceph_conf()
    distribute_ceph_conf()
