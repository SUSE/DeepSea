from ext_lib.utils import runner
from salt.client import LocalClient

# Downside of calling runners from runners and that every runner is selfcontained (in terms of module/pillar sync) is that we now check the dir checksums for every call here


def deploy_core():
    print("may check for updates before")
    foo = runner(__opts__)
    foo.cmd('mon.deploy')
    foo.cmd('mgr.deploy')
    foo.cmd('disks.deploy')


def deploy_services(demo=False):
    """ Just an alias to salt-run services.deploy """
    print("may check for updates before")
    foo = runner(__opts__)
    foo.cmd('services.deploy')


def deploy(demo=False):
    deploy_core()
    deploy_services(demo=demo)


# I'm not quite convinced that this is the right interface to go with.
# salt-run ceph.deploy (core and services)
# salt-run ceph.services (services) -> has no 'deploy' in name
# salt-run ceph.bootstrap

# maybe it should be
# salt-run deploy.core
# salt-run deploy.services
# salt-run deploy.ceph

# or even cluster (probably not the right terminology)
# salt-run cluster.core
# salt-run cluster.serivces
# salt-run cluster.bootstrap

# That'd somehow violate the concept of having the component *first* (mon.foo)
# followed by the operation (component.update/deploy)
# is it worth to make this an exception?
# same goes for bootstrap btw


def health():
    ret: str = LocalClient().cmd(
        'roles:master',
        'podman.ceph_cli', [
            'registry.suse.de/devel/storage/6.0/images/ses/6/ceph/ceph',
            'health'
        ],
        tgt_type='pillar')

    # TODO: improve the extraction, this will eventually fail
    status = list(ret.values())[0].strip()
    if status == 'HEALTH_OK' or status == 'HEALTH_WARN':
        print(f"Ceph cluster status is {status}")
        return True

    print(f"Ceph cluster status is {status}")
    return False
