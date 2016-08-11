# Pillar Prototype
These salt files are intended to allow the creation and management of multiple ceph clusters with a single salt master.

The [diagram](pillar-proposal.png) should explain the intended flow for the orchestration runners and related salt states.

## Status
This is alpha at best.  It works, but runners need refactoring, commenting, correct returns and unit tests.  Several decisions still remain and a few files have notes alluding to missing functionality.  Only a single cluster named `ceph` has been tested.

## Usage

- Install salt-master on one host
- Install salt-minion on all the other hosts you want to be ceph nodes, and *also* on the master host
- Clone this repository and copy the contents i.e. /etc and /srv in their respective directories
- Be sure to have python-pip and git-core installed
- Install https://github.com/oms4suse/python-ceph-cfg on all hosts. If salt-minion is installed on all hosts & keys 
accepted, this can be done by doing salt "*" pip.install git+https://github.com/oms4suse/python-ceph-cfg 
- Copy etc/salt/master.d/reactor.conf-example to /etc/salt/master.d/reactor.conf on the master, or set "startup_states: 'highstate'" in all the minion configs.
- Accept all the salt keys on the master, make sure salt works (`salt '*' test.ping`)
- Create an SLS file in /srv/pillar/ceph/cluster/ for each host, indicating what cluster the host belongs to.
  - The easy way to do this is to just run `salt-run bootstrap.all`, which will make all salt minions ceph cluster nodes. Note that `/srv/modules` needs to be added in `extension_modules` in the salt-master configuration. 
  - If you don't want to use all your minions for the cluster, use the
    bootstrap.selection runner. The runner expects a compound target selector as
    parameter (regarding compound targets refer to
    https://docs.saltstack.com/en/latest/topics/targeting/compound.html).
  - Alternately, you can create the files manually.  For each one, the file should contain just the line "cluster: ceph".  For the admin node (or salt master), use "cluster: unassigned".
- If necessary edit the sntp invocation in /srv/salt/ceph/sync/init.sls to point to a real NTP server (it tries to use the host named 'salt' by default).
- Run `salt-run state.orchestrate ceph.stage.0`
- Run `salt-run state.orchestrate ceph.stage.1`
- Verify /srv/pillar/ceph/stack/ files are populated as mentioned in the [diagram](pillar-proposal.png).
- Edit /srv/pillar/ceph/stack/{ceph.cfg,core.yml,defaults/ceph-custom.yml} to pick up the desired layout and storage files (you need to uncomment whatever sections make sense in ceph.cfg), and set network interfaces if necessary.
- Be sure to add you master_node in startup_states: pillar/ceph/stack/default/global.yml
- Copy either /srv/pillar/ceph/proposals/generic-hostnames.example or /srv/pillar/ceph/proposals/rolebased-hostnames.example to /srv/pillar/ceph/proposals/policy.cfg
- Adapt your policy.cfg to match your cluster topology.
- Just in case, run `salt '*' saltutil.refresh_pillar`.
- Run `salt-run state.orchestrate ceph.stage.2`
- Verify /srv/pillar/ceph/stack/cluster/ceph.conf.yml looks sane (it should havecluster_network, public_network, mon_host and mon_initial_members filled in).
- Run `salt-run state.orchestrate ceph.stage.3`
- You should now have a running cluster.
