import salt.client
import sys
import os


def _preserve_order_sorted(seq):
    """
    Getting rid of duplicates in python could be solved by
    casting a list() to a set() and back to a list()
    `list(set(list_in_question))`
    This method will mess with the sorting though.
    As we rely on the sorting in this scenario, we have to use this
    helper.
    """
    seen = set()
    return [x for x in seq if x not in seen and not seen.add(x)]


def unique(cluster='ceph', exclude=None):
    """
    Assembling a list of nodes.
    Ordered(MON, OSD, MDS, RGW, IGW)
    """
    all_clients = []

    client = salt.client.LocalClient(__opts__['conf_file'])

    cluster_assignment = "I@cluster:{}".format(cluster)
    roles = ['mon', 'storage', 'mds', 'rgw', 'igw', 'ganesha']
    # Adding an exclude param here to allow skipping of individual
    # roles.
    # Usecase: If an admin wants to have manual control over the upgrade
    # process in missioncritical connections like iscsi where one needs
    # to be sure that the MPIO successfully failed over before re booting/starting
    # the service.

    # When search matches no minions, salt prints to stdout.  Suppress stdout.
    _stdout = sys.stdout
    sys.stdout = open(os.devnull, 'w')

    exclude = exclude or []
    roles = [role for role in roles if role not in exclude]
    for role in roles:
        nodes = client.cmd("I@roles:{} and {}".format(role, cluster_assignment), 'pillar.get', ['roles'], expr_form="compound")
        all_clients += nodes.keys()

    sys.stdout = _stdout
    return _preserve_order_sorted(all_clients)
