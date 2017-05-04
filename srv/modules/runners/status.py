import salt.client

def report(cluster_name='ceph'):
    """
    Scans for:
    * OS Version and Codename
    * Ceph version
    * Salt version
    and generates a report
    """
    local = salt.client.LocalClient()
    status_report = {}
    search = "I@cluster:{}".format(cluster_name)
    os_codename = local.cmd(search, 'grains.get', [ 'oscodename' ], expr_form="compound")
    ceph_version = local.cmd(search, 'cmd.run', [ 'ceph --version' ], expr_form="compound")
    salt_version = local.cmd(search, 'grains.get', [ 'saltversion' ], expr_form="compound")

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
