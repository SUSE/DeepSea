import salt.client
from collections import Counter


def _get_data(cluster_name='ceph'):
    local = salt.client.LocalClient()
    status_report = {}
    search = "I@cluster:{}".format(cluster_name)
    # grains might be inaccurate or not up to date because they are designed to hold static data about
    # the minion. In case of an update though, the data will change.
    # grains are refreshed on reboot(restart of the service).
    os_codename = local.cmd(search, 'grains.get', [ 'oscodename' ], expr_form="compound")
    salt_version = local.cmd(search, 'grains.get', [ 'saltversion' ], expr_form="compound")
    ceph_version = local.cmd(search, 'cmd.shell', [ 'ceph --version' ], expr_form="compound")

    return os_codename, salt_version, ceph_version

def longreport(cluster_name='ceph'):
    """
    Scans for:
    * OS Version and Codename
    * Ceph version
    * Salt version
    and generates a report
    """
    
    status_report = {}

    os_codename, salt_version, ceph_version = _get_data(cluster_name)
    # Safely pre-populating the dict as 'search' is equivalent for all queries
    for node in os_codename.keys():
       status_report[node] = {}
    
    for node,key in os_codename.iteritems():
       status_report[node]['os_version'] = key
    for node,key in ceph_version.iteritems():
       status_report[node]['ceph_version'] = key
    for node,key in salt_version.iteritems():
       status_report[node]['salt_version'] = key

    return status_report

def summary(cluster_name='ceph'):
    """
    Creates a report that tries to find the most common versions from:
      * OS Version and Codename
      * Ceph version
      * Salt version
    and prints it out.
    In addition you will also be presented with the minions that don't match
    one of the most_common_versions
    """
    os_codename, salt_version, ceph_version = _get_data(cluster_name)

    unsynced_nodes = {'out of sync': []}
    common_keys = {'ceph': {}, 'salt': {}, 'os': {}}

    def _organize(minion_data):
        key_ident = minion_data[0]
        minion_data_dct = minion_data[1]
        counter_obj = Counter(minion_data_dct.values())
        if counter_obj.most_common():
            most_common_item = counter_obj.most_common()[0][0]
        common_keys.update({key_ident: most_common_item})
        for node, value in minion_data_dct.iteritems():
            if value != most_common_item:
                if node not in unsynced_nodes:
                    unsynced_nodes['out of sync'].append(node)

    for minion_data in [('os', os_codename), ('ceph', ceph_version), ('salt', salt_version)]:
        _organize(minion_data)
        
    return {'statusreport': [unsynced_nodes, common_keys]}
