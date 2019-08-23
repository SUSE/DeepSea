from ext_lib.utils import runner, prompt, log_n_print
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
TODO: Make the time-server thing separate
* SSL-certificates
"""

proposals_dir = '/srv/pillar/ceph/proposals'
policy_path = f'{proposals_dir}/policy.cfg'


# maybe outsource
def _read_policy_cfg():
    with open(policy_path, 'r') as _fd:
        return _fd.read()


# outsource
def run_and_eval(runner_name, extra_args=None):
    # maybe supress the 'True' output from the screen
    qrunner = runner(__opts__)
    if not qrunner.cmd(runner_name, extra_args):
        log_n_print(f"{runner_name} failed.")
        raise Exception()


def ceph(non_interactive=False):
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
    if not exists(proposals_dir):
        log_n_print("Creating proposals directory.")
        run_and_eval('populate.proposals')
    else:
        log.debug("Found a proposals directory")

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
    log_n_print("We'll now we update the pillar with the your changes.")
    pillar_questioneer(non_interactive=non_interactive)
    log_n_print("Ok, let's verify the network settings")
    log_n_print("This is the network configuration we detected.")
    run_and_eval('advise.networks')
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
        "TEMP: Creating the ceph.conf (will go away in further releases)")
    run_and_eval('config.deploy')

    # TODO: Break all(sysexit) on SIGINT
    print("Bootstrapping monitors..")
    run_and_eval('mon.deploy',
                 [f'bootstrap=True, non_interactive={non_interactive}'])

    # if the answer in mon.deploy is 'no'. It will still deploy the managers.. Handle global signals/returns
    print("Bootstrapping mgrs..")
    run_and_eval("mgr.deploy", [f'non_interactive={non_interactive}'])

    run_and_eval("ceph.health")

    print(
        "Bootstrapping is complete now. Please proceed with the osd.deploy/help command."
    )

    return True


# TODO:
#   When to update the /srv/pillar/ struct. Previously we did that in every stage.1 invocation
#   We may keep track of the salt-key -L ('inventory')


def cluster():
    ceph()
