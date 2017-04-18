# DeepSea
A collection of Salt files for deploying, managing and automating Ceph.

The goal is to manage multiple Ceph clusters with a single salt master.  At this time, only a single Ceph cluster can be managed.

The [diagram](deepsea.png) should explain the intended flow for the orchestration runners and related salt states.

## Status
Automatic discovery, configuration and deployment of Ceph clusters works. RGW
deployment works for single site deployements. MDS deployment and CephFS creation works.

## Get Involved
To learn more about DeepSea, take a look at the [Wiki](https://github.com/SUSE/DeepSea/wiki).

There is also a dedicated mailing list [deepsea-users](http://lists.suse.com/mailman/listinfo/deepsea-users).
If you have any questions, suggestions for improvements or any other
feedback, please join us there! We look forward to your contribution.

If you think you've found a bug or would like to suggest an enhancement, please submit it via the [bug tracker](https://github.com/SUSE/DeepSea/issues/new) on GitHub.

For contributing to DeepSea, refer to the [contribution guidelines](https://github.com/suse/deepsea/blob/master/contributing.md)

## Usage
### Prepare Salt
#### Install and configure the Salt master
- Install salt-master on one host. We shall refer to this host as the
  `admin node`.
- It is a recommended best practice to have a management network for Ceph to
  prevent management traffic from interfering with Ceph data traffic. If you
  have a network designated for management traffic, configure
  the Salt master process to communicate only on the cluster's management
  interface. This can be done by adding a file
  `/etc/salt/master.d/interface.conf` with the content below where `X.X.X.X`
  is the IP address of the `admin node` on the management network.
  ```
  interface: X.X.X.X
  ```
- It may be useful to add the `salt` network alias for the `admin node`, as
  `salt` is the name of the Salt master minions will try to connect with by
  default.
#### Install and configure the Salt minions
- Install salt-minion on all hosts including the `admin node`.
- From the `admin node`, accept the Salt keys for all nodes in the Ceph cluster
  (e.g. `salt-key -A -y`)
- If you choose not to add the `salt` network alias for the `admin node`, you
  will need to edit the file `/etc/salt/minion` on each minion and update the
  `master` option to refer to the `admin node`.
#### A theoretical example
Note that this example is too small to work in reality. It is only to
demonstrate the practical concepts.
- This is a snippet from an example `/etc/hosts` file for our theoretical Ceph
  cluster. You can see the `salt` alias for the `admin node` on the management
  interface.
  ```
  192.168.10.254  admin-management admin.ceph salt
  192.168.10.11   mon1-management mon1.ceph
  192.168.10.21   data1-management data1.ceph

  172.16.1.254    admin-public admin admin.ceph
  172.16.1.11     mon1-public mon1 mon1.ceph
  172.16.1.21     data1-public data1 data1.ceph

  172.16.2.254    admin-cluster admin.ceph
  172.16.2.11     mon1-cluster mon1.ceph
  172.16.2.21     data1-cluster data1.ceph
  ```
- `/etc/salt/master.d/interface.conf` in our example would be
  ```
  # IP address of admin node on management network
  interface: 192.168.10.254
  ```
- After accepting the Salt keys on the master, you can execute the command
  `salt-key --list-all` on the `admin node`, and you should see that each minion
  is listed under `Accepted Keys` and that each minion has the same id as
  is demonstrated for our theoretical cluster. (Each entry under `Accepted
  Keys` is a `minion id` by which Salt and DeepSea will target the node)
  ```
  > salt-key --list-all
  Accepted Keys:
  admin.ceph
  data1.ceph
  mon1.ceph
  Denied Keys:
  Unaccepted Keys:
  Rejected Keys:
  ```

### Install DeepSea
- Install [rpm](https://build.opensuse.org/package/show/home:swiftgist/deepsea)
- For non-RPM-distros, try `make install`.

### Configure
- DeepSea needs to know which node will act as the Salt master.
  To avoid any possible user confusion, DeepSea enforces that all minion
  hostnames (including the `admin node`'s hostname) should match the minion id.
  Edit [/srv/pillar/ceph/master_minion.sls](srv/pillar/ceph/master_minion.sls),
  and ensure the value of `master_minion` matches the minion id for the
  `admin node`. (In our example from __Prepare Salt__ above, the value should be
  `admin.ceph`.)

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

Please refer to the [Policy wiki page](https://github.com/SUSE/DeepSea/wiki/policy)
for more detailed information.

## Test intial deployment and generating load
Once a cluster is deployed one might want to verify functionality or run
benchmarks to verify the cluster works as expected.
- In order to gain some confidence in your cluster after the inital deployment
  (stage 3) run `salt-run state.orch ceph.benchmarks.baseline`. This runs an osd
  benchmark on each OSD and aggregates the results. It reports your average OSD
  performance and points out OSDs that deviate from the average. *Please note
  that for now the baseline benchmark assumes all uniform OSDs.*
- To load test CephFS run `salt-run state.orch ceph.benchmarks.cephfs`.
  This requires a running MDS (deploy in stage 4) and at least on minion with
  the mds-client role. The cephfs_benchmark stage will then mount the CephFS
  instance on the mds-client and run a bunch of fio tests. See the [benchmark
  readme](srv/pillar/ceph/benchmark/README.md) for futher details.
- *more to come*
