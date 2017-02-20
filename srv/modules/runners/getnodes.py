import salt.client


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


def sorted_unique_nodes(cluster=None):
    """ 
    Assembling a list of nodes.
    Ordered(MON < OSD < MDS < RGW < IGW)  
    """ 
    all_clients = []

    client = salt.client.LocalClient(__opts__['conf_file'])

    cluster_assignment = "I@cluster:{}".format(cluster)
    roles = ['mon', 'storage', 'mds', 'rgw', 'igw', 'ganesha']
    for role in roles:
         dct = client.cmd("I@roles:{} and {}".format(role, cluster_assignment), 'pillar.get', ['roles'], expr_form="compound")
         all_clients += dct.keys()
    return _preserve_order_sorted(all_clients)
