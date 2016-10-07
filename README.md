# DeepSea
A collection of Salt files for deploying, managing and automating Ceph.

These goal is to manage multiple Ceph clusters with a single salt master.  At this time, only one Ceph cluster is managed.

The [diagram](deepsea.png) should explain the intended flow for the orchestration runners and related salt states.

## Status
Automatic discovery, configuration and deployment of Ceph clusters works. RGW
deployment is currently broken. MDS deployment and CephFS creation works.


## Usage
### Prepare Salt
- Install salt-master on one host
- Install salt-minion on all hosts including the master.
- Accept keys (e.g. `salt-key -A -y`)

### Install DeepSea
- Install [rpm](https://build.opensuse.org/package/show/home:swiftgist/deepsea)
- For non-RPM-distros, try `make install`.

### Configure
- Edit [/srv/pillar/ceph/master_minion.sls](srv/pillar/ceph/master_minion.sls)

### Steps
- Run `salt-run state.orch ceph.stage.0` or `salt-run state.orch ceph.stage.prep`
- Run `salt-run state.orch ceph.stage.1` or `salt-run state.orch ceph.stage.discovery`
- Create `/srv/pillar/ceph/proposals/policy.cfg`.  Examples are [here](doc/examples)
- Run `salt-run state.orch ceph.stage.2` or `salt-run state.orch ceph.stage.configure`
- Run `salt-run state.orch ceph.stage.3` or `salt-run state.orch ceph.stage.deploy`
- Run `salt-run state.orch ceph.stage.4` or `salt-run state.orch ceph.stage.services`

### Details on policy.cfg
The discovery stage (or stage 1) creates many configuration proposals under
`/srv/pillar/ceph/proposals`. The files contain configuration options for Ceph
clusters, potential storage layouts and role assignments for the cluster
minions. The policy.cfg specifies which of these files and options are to be
used for the deployment.

*to be extended*

## Generating Load
Once a cluster is deployed one might want to generate some load or run
benchmarks to verify the cluster works as expected.
- To load test CephFS run `salt-run state.orch ceph.benchmarks.cephfs`.
  This requires a running MDS (deploy in stage 4) and at least on minion with
  the mds-client role. The cephfs_benchmark stage will then mount the CephFS
  instance on the mds-client and run a bunch of fio tests. See the [benchmark
  readme](srv/pillar/ceph/benchmark/README.md) for futher details.
- *more to come*
