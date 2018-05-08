import salt.client

from subprocess import check_output

def run(**kwargs):
    args = {'cmd': 'echo no command supplied'}
    args.update(kwargs)
    local_client = salt.client.LocalClient()
    master_minion = local_client.cmd(
        'I@roles:master', 'pillar.get',
        ['master_minion'], expr_form='compound').items()[0][1]
    output = local_client.cmd(master_minion, 'cmd.shell', [args['cmd']], expr_form='compound')
    # only return the result from the salt master
    # TODO generalize to run commands on any minion
    return next(iter(output.values()))
