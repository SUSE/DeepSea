from ext_lib.utils import runner, prompt
from ext_lib.hash_dir import pillar_questioneer, module_questioneer
from pydoc import pager
from os.path import exists
from salt.client import LocalClient

import signal
import sys

# We have to take care of the one-time operations that need to be done before a deployment


def handle_ctrl_c(signal, frame):
    print("Got ctrl+c, going down!")
    sys.exit(1)


signal.signal(signal.SIGINT, handle_ctrl_c)
"""

TODO: Make the time-server thing separate

* Update the host system
* Populate the proposals (salt-run populate.proposals)
* Scan for the networks (maybe ask the user this time?)
* SSL-certificates


"""

proposals_dir = '/srv/pillar/ceph/proposals'
policy_path = f'{proposals_dir}/policy.cfg'


def _read_policy_cfg():
    with open(policy_path, 'r') as _fd:
        return _fd.read()


def _get_public_address():
    __salt__['public.address']


def ceph(non_interactive=False):
    module_questioneer(non_interactive=non_interactive)
    print("TODO make sure that podman is installed")
    print("TODO zypper in -t pattern apparmor")
    # or add suse-certs repo and install SUSE-CA
    print(
        "TODO podman pull registry.suse.de/devel/storage/6.0/images/ses/6/ceph/ceph --tls-verify=false"
    )
    print(
        "Print a basic help thing explaining the steps and asking for a timeserver"
    )
    qrunner = runner(__opts__)
    if not exists(proposals_dir):
        print("Creating proposals directory.")
        qrunner.cmd('populate.proposals')
    else:
        print("Found a proposals directory")

    if not exists(policy_path):
        print(
            f"You don't appear to have a policy.cfg. Please create it under the proposals directory '{proposals_dir}' and re-run this command"
        )
        print(f"You can find guidance on how to do that here: TODO")
        return False
    else:
        print("Found a policy.cfg.")
        if prompt(
                "Do you want to verify the content?",
                non_interactive=non_interactive,
                default_answer=False):
            pager(_read_policy_cfg())
            if not prompt("Do you want to continue?"):
                return 'aborted'
    print("We'll now we update the pillar with the your changes.")
    pillar_questioneer(non_interactive=non_interactive)
    print("Ok, let's verify the network settings")
    print("This is the network configuration we detected.")
    qrunner.cmd('advise.networks')
    if prompt(
            "Do you want to adapt this setting?",
            non_interactive=non_interactive,
            default_answer=False):
        print(
            'dummy for proposals/config/stack/default/ceph/cluster.yml:public_network manipulation'
        )
        print("We'll now we update the pillar with the your changes.")
        pillar_questioneer(non_interactive=non_interactive)
    print("TEMP: Creating the ceph.conf (will go away in further releases)")
    qrunner.cmd('config.create_and_distribute_ceph_conf')

    # TODO: Break all(sysexit) on SIGINT
    print("Bootstrapping monitors..")
    qrunner.cmd('mon.deploy',
                ["bootstrap=True", f"non_interactive={non_interactive}"])
    # if the answer in mon.deploy is 'no'. It will still deploy the managers.. Handle global signals/returns
    print("Bootstrapping mgrs..")
    qrunner.cmd('mgr.deploy', [f"non_interactive={non_interactive}"])


#     print("If policty.cfg and proposals dir is not present")
#     print("qrunner.cmd('host.update')")
#     print("Ask the user to create(adapt) a policy.cfg. Exit and ask to re-run this command")
#     print("This is now the entry point for the second invocation")
#     print("Use salt-run advise-networks to ask user if that's the right networks")
#     print("Tell user where mon and mgrs will be deployed")
#     print("Do it with interactive mode")
#     print("After successful deploy. Guide towards osd.deploy and drivegroups (wiki)")
#     print("From there on every command (mon/osd/mgr) should be selfcontained and doesn't require an additional step")
#     print("I.e. adding a MON. 1) Adapt the policy.cfg 2) Run mon.deploy")

#     print(""" Open questions:

#     When to update the /srv/pillar/ struct. Previously we did that in every stage.1 invocation
#     We may keep track of the salt-key -L ('inventory')
# """)


def cluster():
    ceph()
