from ext_lib.utils import runner, prompt, log_n_print, run_and_eval, _query_master_pillar, ceph_health
from ext_lib.hash_dir import pillar_questioneer, module_questioneer
from pydoc import pager
from os.path import exists
from salt.client import LocalClient
import logging
import signal
import sys

log = logging.getLogger(__name__)


def handle_ctrl_c(signal, frame):
    print("Got ctrl+c, going down!")
    sys.exit(1)


signal.signal(signal.SIGINT, handle_ctrl_c)
"""

TODO:
Make the time-server thing separate
* SSL-certificates

"""

# FIXME: master can't be contacted before policy.cfg exists, probably read from internal.yml file
policy_path = '/srv/pillar/ceph/proposals/policy.cfg' #_query_master_pillar('deepsea_policy_path')
proposals_dir =  '/srv/pillar/ceph/proposals'# _query_master_pillar('deepsea_proposal_dir')

def _read_policy_cfg():
    with open(policy_path, 'r') as _fd:
        return _fd.read()


def initialize(non_interactive=False):
    module_questioneer(non_interactive=non_interactive)
    log_n_print(
        "TODO: check for deepsea_minions, There is a validate.deepsea_minions, check that"
    )
    run_and_eval("host.install_common_packages")
    run_and_eval('host.update', ['parallel=True'])

    log_n_print(
        "TODO: podman pull registry.suse.de/devel/storage/6.0/images/ses/6/ceph/ceph --tls-verify=false"
    )
    log_n_print(
        "TODO: print a basic help thing explaining the steps and asking for a timeserver"
    )
    return True


def setup(non_interactive=False):
    if not exists(policy_path):
        log_n_print(
            f"You don't appear to have a policy.cfg. Please create it under the proposals directory '{proposals_dir}' and re-run this command"
        )
        log_n_print(f"You can find guidance on how to do that here: TODO")
        return False
    else:
        log_n_print("Found a policy.cfg.")
        if prompt(
                "Do you want to verify the content?",
                non_interactive=non_interactive,
                default_answer=False):
            pager(_read_policy_cfg())
            if not prompt("Do you want to continue?"):
                return 'aborted'
    run_and_eval("config.deploy_salt_conf")
    log_n_print("Updating the pillar with your changes.")
    pillar_questioneer(non_interactive=non_interactive)
    log_n_print("TODO: pillarquery the network interfaces")
    if prompt(
            "Do you want to adapt this setting?",
            non_interactive=non_interactive,
            default_answer=False):
        log_n_print(
            'dummy for proposals/config/stack/default/ceph/cluster.yml:public_network manipulation'
        )
        log_n_print("We'll now we update the pillar with the your changes.")
        pillar_questioneer(non_interactive=non_interactive)
    log_n_print(
        "TEMP: Creating and distributing the ceph.conf (will go away in further releases)"
    )
    run_and_eval("config.deploy_ceph_conf")

    return True


def core(non_interactive=False):
    # TODO: Break all(sysexit) on SIGINT
    print("Bootstrapping monitors..")
    run_and_eval('mon.deploy',
                 [f'bootstrap=True', f'non_interactive={non_interactive}'])

    # FIXME: if the answer in mon.deploy is 'no'. It will still deploy the managers.. Handle global signals/returns
    print("Bootstrapping mgrs..")
    run_and_eval("mgr.deploy", [f'non_interactive={non_interactive}'])


    if ceph_health():
        print(
            "Bootstrapping is complete now. Please proceed with the osd.deploy/help command."
        )
        return True
    print("Bootstrapping failed. TODO write a meaningful error message")
    return False


def ceph(non_interactive=False):
    # TODO: improve return messages
    # if not initialize(non_interactive=non_interactive):
    #     return False
    if not setup(non_interactive=non_interactive):
        return False
    if not core(non_interactive=non_interactive):
        return False

    # TODO: When to update the /srv/pillar/ struct. Previously we did that in every stage.1 invocation
    # We may keep track of the salt-key -L ('inventory') periodically

    # TODO: return correct status
    return True


def cluster():
    ceph()
