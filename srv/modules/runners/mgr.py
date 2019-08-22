from ext_lib.hash_dir import pillar_questioneer, module_questioneer
from ext_lib.utils import evaluate_module_return
from salt.client import LocalClient


def deploy(non_interactive=False):
    pillar_questioneer(non_interactive=False)
    module_questioneer(non_interactive=False)
    print("Deploying mgrs..")
    ret: str = LocalClient().cmd(
        "I@roles:mgr",
        'podman.create_mgr',
        ['registry.suse.de/devel/storage/6.0/images/ses/6/ceph/ceph'],
        tgt_type='compound')

    if not evaluate_module_return(ret):
        return False
    print("Mgr created")
    return True
