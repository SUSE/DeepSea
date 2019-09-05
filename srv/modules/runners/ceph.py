from ext_lib.utils import runner, run_and_eval
from salt.client import LocalClient

# Downside of calling runners from runners and that every runner is selfcontained (in terms of module/pillar sync) is that we now check the dir checksums for every call here


def deploy_core():
    print("may check for updates before")
    run_and_eval('mon.deploy')
    run_and_eval('mgr.deploy')
    # NOT IMPLEMENTED #
    # run_and_eval('disks.deploy')
    # NOT IMPLEMENTED #


def deploy_services(demo=False):
    """ Just an alias to salt-run services.deploy """
    print("may check for updates before")
    run_and_eval('services.deploy')


def deploy(demo=False):
    deploy_core()
    deploy_services(demo=demo)


def purge():
    # NOT IMPLEMENTED #
    # run_and_eval('igw.remove', ['purge=True'])
    # run_and_eval('nfs.remove', ['purge=True'])
    # run_and_eval('rgw.remove', ['purge=True'])
    # run_and_eval('mds.remove', ['purge=True'])
    # run_and_eval('osd.remove', ['purge=True'])
    # NOT IMPLEMENTED #

    run_and_eval('mgr.remove', ['purge=True'])
    run_and_eval('mon.remove', ['purge=True'])

    # NOT IMPLEMENTED #
    # run_and_eval('monitoring.remove', ['purge=True'])
    # NOT IMPLEMENTED #

    # TODO: finally remove old keyrings, directories etc


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
