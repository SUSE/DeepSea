from ext_lib.hash_dir import pillar_questioneer, module_questioneer
from ext_lib.utils import _deploy_role, _remove_role
from salt.client import LocalClient

# TODO: The non_interactive passing is weird..
# change that by abstracting to a class or a config option

def deploy(non_interactive=False):
    pillar_questioneer(non_interactive=non_interactive)
    module_questioneer(non_interactive=non_interactive)
    return _deploy_role(role='mgr', non_interactive=non_interactive)


def remove(non_interactive=False):
    pillar_questioneer(non_interactive=non_interactive)
    return _remove_role(role='mgr', non_interactive=non_interactive)


def update():
    # TODO: implementation
    """ How to query/pull from the registry? """
    pass
