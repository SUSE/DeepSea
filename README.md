# DeepSea
A collection of Salt files for deploying, managing and automating Ceph.

These goal is to manage multiple ceph clusters with a single salt master.  At this time, only one Ceph cluster is managed.

The [diagram](deepsea.png) should explain the intended flow for the orchestration runners and related salt states.

## Status
The stages 0-4 which covers optional provisioning to creating gateways for Ceph services are working.  Role removal is in progress.


## Usage
Prepare Salt
- Install salt-master on one host
- Install salt-minion on all hosts including the master.
- Accept keys (e.g. salt-key -A -y)

Install DeepSea
- Install rpm (link TBD)

Configure
- Edit /etc/salt/master.d/logging.conf
- Edit /srv/pillar/ceph/master_minion.sls

Steps
- Run `salt-run state.orch ceph.stage.0 or salt-run state.orch ceph.stage.prep`
- Run `salt-run state.orch ceph.stage.1 or salt-run state.orch ceph.stage.discovery`
- Create /srv/pillar/ceph/proposals/policy.cfg.  Examples are in ...
- Run `salt-run state.orch ceph.stage.2 or salt-run state.orch ceph.stage.configure`
- Run `salt-run state.orch ceph.stage.3 or salt-run state.orch ceph.stage.deploy`
- Run `salt-run state.orch ceph.stage.4 or salt-run state.orch ceph.stage.services`

