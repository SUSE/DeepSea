from salt.client import LocalClient
from subprocess import Popen
import pydoc


def help():
    try:
        pydoc.doc('deepsea.monitoring')
    except ImportError:
        # Add template around help text to make this consistent
        pydoc.pager('Custom Pager when there is no deepsea monitoring man page yet')

def deploy():
    # Steps
    # 1) # install and setup node exporters
    # state ceph.monitoring.prometheus.exporters.node_exporters on all_nodes

    install_setup_node_exporter()
    # 2)
    # essentially what's in ceph.stage.3.monitoring
    populate_scrape_configs()
    populate_altermanager_peers()
    return True


def install_setup_node_exporter():
    # TODO adapt that to use containers
    print("Setting up and installing node_exporter")
    local_client = LocalClient()
    ret = local_client.cmd(
        'I@cluster:ceph', # TODO change to deepsea_minions?
        'state.apply', ['ceph.monitoring.prometheus.exporters.node_exporter'],
        tgt_type='compound')
    return True
    # TODO ret eval


def populate_scrape_configs():
    print("Populating scrape configs")
    local_client = LocalClient()
    ret = local_client.cmd(
        'I@roles:master',
        'state.apply', ['ceph.monitoring.prometheus.populate_scrape_configs'],
        tgt_type='compound')
    return True
    # TODO ret eval

def populate_altermanager_peers():
    print("Populate altermanager peers")
    local_client = LocalClient()
    ret = local_client.cmd(
        'I@roles:master',
        'state.apply', ['ceph.monitoring.prometheus.populate_peers'],
        tgt_type='compound')
    return True
    # TODO ret eval


# etc etc etc





def update():
    pass
