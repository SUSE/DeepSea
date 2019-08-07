from ext_lib.utils import cluster_minions
from salt.client import LocalClient


def update(*args, **kwargs):

    # general question:
    # should we rely on self provided states or just call pkg.uptodate in this module
    # pro: no extra state to maintain
    # con: we can't change the parameter passed to pkg.uptodate

    parallel = kwargs.get('parallel', False)
    local_client = LocalClient()
    if args:
        print(f"Limiting update task to minions {args[0]}")
        ret = local_client.cmd(
            args[0],
            'state.apply', ['ceph.updates.regular'],
            tgt_type='compound')
        # TODO: improve error checking
        # NOTE: return string vs return bool
        return 'success'

    minions_to_update = cluster_minions()
    if parallel:
        print("Updating all minions at once, please use with caution")
        ret = local_client.cmd(
            minions_to_update,
            'state.apply', ['ceph.updates.regular'],
            tgt_type='list')
        # TODO: improve error checking
        return True

    for minion in minions_to_update:
        print(f"Updating {minion}")
        ret = local_client.cmd(
            minion, 'state.apply', ['ceph.updates.regular'], tgt_type='glob')

        # extract salt return evaluation into a separate util function
        metadata = ret.get(minion, '')
        if not metadata:
            print("Could not extract data from salt's return")
            return False
        upgrade_metadata = list(metadata.values())
        if not upgrade_metadata:
            print("Could not extract data from salt's return")
            return False

        if not upgrade_metadata[0].get('result', False):
            print("Salt reported that the update failed.")
            print(f"salt said: {upgrade_metadata[0].get('comment', '')}")
            return False

        print(f"salt said: {upgrade_metadata[0].get('comment', '')}")
        print(f"Updated {minion}")
    return True
