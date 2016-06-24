# Pillar Prototype
These salt files are intended to allow the creation and management of multiple ceph clusters with a single salt master.  

The [diagram](pillar-proposal.png) should explain the intended flow for the orchestration runners and related salt states.

## Status
This is alpha at best.  It works, but runners need refactoring, commenting, correct returns and unit tests.  Several decisions still remain and a few files have notes alluding to missing functionality.  Only a single cluster named `ceph` has been tested.

## Usage

- Install salt-master on one host
- Install salt-minion on all the other hosts you want to be ceph nodes, and *also* on the master host
- Install https://github.com/oms4suse/python-ceph-cfg on all hosts.
- Copy etc/salt/master.d/reactor.conf-example to /etc/salt/master.d/reactor.conf on the master, or set "startup_states: 'highstate'" in all the minion configs.
- Accept all the salt keys on the master, make sure salt works (`salt '*' test.ping`)
- Copy the srv tree from this repo to /srv on the salt master (be careful if you're copying onto an existing salt master which already has top.sls files and whatnot).
- Create an SLS file in /srv/pillar/ceph/cluster/ for each host, indicating what cluster the host belongs to.
  - The easy way to do this is to just run `salt-run bootstrap.all`, which will make all salt minions ceph cluster nodes.
  - Alternately, you can create the files manually.  For each one, the file should contain just the line "cluster: ceph".  For the admin node (or salt master), use "cluster: unassigned".
- If necessary edit the sntp invocation in /srv/salt/ceph/sync/init.sls to point to a real NTP server (it tries to use the host named 'salt' by default).
- Run `salt-run state.orchestrate ceph.stage0`
- Run `salt-run state.orchestrate ceph.stage1`
- Verify /srv/pillar/ceph/stack/ files are populated as mentioned in the [diagram](pillar-proposal.png).
- Edit /srv/pillar/ceph/stack/{ceph.cfg,core.yml,defaults/ceph-custom.yml} to pick up the desired layout and storage files (you need to uncomment whatever sections make sense in ceph.cfg), and set network interfaces if necessary.
- Just in case, run `salt '*' saltutil.refresh_pillar`.
- Run `salt-run state.orchestrate ceph.stage2`
- Verify /srv/pillar/ceph/stack/cluster/ceph.conf.yml looks sane (it should havecluster_network, public_network, mon_host and mon_initial_members filled in).
- Run `salt-run state.orchestrate ceph.stage3`
- You should now have a running cluster.
