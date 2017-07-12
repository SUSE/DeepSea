# DeepSea
A collection of Salt files for deploying, managing and automating Ceph.

The goal is to manage multiple Ceph clusters with a single salt master. At this time, only a single Ceph cluster can be managed.

The [diagram](deepsea.png) should explain the intended flow for the orchestration runners and related salt states.

## Status
DeepSea currently supports the following functionality:

- Automatic discovery, deployment, configuration and life cycle management of Ceph clusters
- Initial support for importing Ceph clusters deployed using `ceph-deploy`
- RADOS Gateway deployment (for single site deployments)
- CephFS MDS deployment and CephFS creation
- Sharing CephFS or S3 buckets via NFS Ganesha
- iSCSI target management via [lrbd](https://github.com/SUSE/lrbd/)
- Deployment and configuration of [Prometheus](https://prometheus.io/) and [Grafana](https://grafana.com/) for monitoring / performance data visualization
- Deployment and configuration of [openATTIC](https://openattic.org/) for web-based management and monitoring of Ceph resources

## Get Involved
To learn more about DeepSea, take a look at the [Wiki](https://github.com/SUSE/DeepSea/wiki).

There is also a dedicated mailing list [deepsea-users](http://lists.suse.com/mailman/listinfo/deepsea-users).
If you have any questions, suggestions for improvements or any other
feedback, please join us there! We look forward to your contribution.

If you think you've found a bug or would like to suggest an enhancement, please submit it via the [bug tracker](https://github.com/SUSE/DeepSea/issues/new) on GitHub.

For contributing to DeepSea, refer to the [contribution guidelines](https://github.com/suse/deepsea/blob/master/contributing.md)

## Usage
You need at least a minimum of 4 nodes to be able to test and use DeepSea properly.
You could set the option `DEV_ENV=true` during the deployment stages to be able to use
less than 4 nodes. 

### Add DeepSea repo to your admin host
- Install [rpm](https://build.opensuse.org/package/show/filesystems:ceph:luminous/deepsea)
- For non-RPM-distros or for the snapshot status, `git clone https://github.com/SUSE/DeepSea.git`, `cd DeepSea`, `make install`.

### Cluster Preparation 
The cluster deployment process has several phases. First, you need to prepare all nodes of the cluster by configuring Salt and then deploy and configure Ceph.
The following procedure describes the cluster preparation in detail.

Install a minimum of four machines (or use `DEV_ENV=true` during the deployment process) with SUSE Leap 42.3 or Tumbleweed and add the DeepSea repo to your defined "admin" node
- `zypper ar http://download.opensuse.org/repositories/filesystems:/ceph:/luminous/openSUSE_Leap_42.3/filesystems:ceph:luminous.repo && zypper ref`

Make sure that each node can resolve the DNS names of all other nodes. If you don't have a DNS Server you could also add all hosts of your cluster to the /etc/hosts file. 
The Salt master needs to resolve all its Salt minions by their host names, as well as all Salt minions need to resolve the Salt master by its host name. 

Configure, enable, and start the NTP time synchronization server on all nodes:
- `systemctl enable ntpd.service`
- `systemctl start ntpd.service`

Check whether the AppArmor service is running and disable it on each cluster node to avoid problems.
- `zypper disable apparmor.service`

Check whether the Firewall service is running and disable it on each cluster node to avoid problems.
- `systemctl disable SuSEfirewall2.service`

Note that the Cluster deployment with DeepSea will not work with Firewall/AppArmor enabled.

Install DeepSea on the node which will be the Salt master:
- `zypper in deepsea`

The command installs the salt-master and salt-minion packages as a dependency as well as Grafana/Prometheus

Check that the salt-master service is enabled and started - enable and start it if needed:
- `systemctl enable salt-master.service`
- `systemctl start salt-master.service`

Install the package salt-minion on all minion nodes.
- `zypper in salt-minion`

Configure all minions (including the master minion) to connect to the master. If your Salt master is not reachable by the DNS name salt, 
edit the file "/etc/salt/minion" or create a new file "/etc/salt/minion.d/master.conf" with the following content:
- `master: DNS_name_of_salt_master`

If you performed any changes to the configuration files mentioned above, restart the Salt service on all Salt minions:
- `systemctl restart salt-minion.service`

Check that the file /srv/pillar/ceph/master_minion.sls on the Salt master points to your Salt master. If your Salt master is reachable via 
more host names, use the one suitable for the storage cluster. If you used the default host name for your Salt master in the example domain, then the file looks as follows:
- `master_minion: salt.example`

Check that the salt-minion service is enabled and started on all nodes. Enable and start it if needed:
- `systemctl enable salt-minion.service`
- `systemctl start salt-minion.service`

Accept all salt keys on the Salt master:
- `salt-key --accept-all`

Verify that the keys have been accepted:
- `salt-key --list-all`

#### Cleanup your Disks - only needed if your disks were used in a cluster before

Prior to deploying a cluster with DeepSea make sure that all disks that were used as OSD by previous clusters are empty without partitions. To ensure this, you have to manually zap all the disks. 
Remember to replace 'X' with the correct disk letter - Attention - This command will remove all your data from a disk, so please be careful:

Wipe the beginning of each partition:

`for partition in /dev/sdX[0-9]
do
  dd if=/dev/zero of=$partition bs=4096 count=1 oflag=direct
done`

Wipe the partition table:
- `sgdisk -Z --clear -g /dev/sdX`

Wipe the backup partition tables:
- `size=`blockdev --getsz /dev/sdX``
- `position=$((size/4096 - 33))`
- `dd if=/dev/zero of=/dev/sdX bs=4096 count=33 seek=$position oflag=direct`

Now you deploy and configure Ceph. Unless specified otherwise, all steps are mandatory.

Note: Salt Command Conventions
There are two possibilities how to run `salt-run state.orch` - one is with `stage.<stage number>`, the other is with a name of the stage. 
Both notations have the same impact and it is fully up to your preferences which command will you use. Both notations are used in the following
deployment steps. So please choose what you prefer.

### Cluster Deployment

#### Stage 0
During this stage all required updates are applied and your system may be rebooted.

- `salt-run state.orch ceph.stage.0` or `salt-run state.orch ceph.stage.prep`

Note: If during Stage 0 the Salt master reboots to load new kernel version, you need to run Stage 0 again, otherwise minions will not be targeted.

#### Stage 1
The discovery stage collects all hardware in your cluster and also collects necessary information for the Ceph configuration. The configuration fragments are stored in the directory /srv/pillar/ceph/proposals. 
The data are stored in the YAML format in *.sls or *.yml files.

- `salt-run state.orch ceph.stage.1` or `salt-run state.orch ceph.stage.discovery`

After the previous command finishes successfully, create a policy.cfg file in /srv/pillar/ceph/proposals.

You can find an example in our [docs](https://github.com/SUSE/DeepSea/blob/master/doc/examples/policy.cfg-rolebased) folder. Please change the example file to fit to your needs.

Example:

- Please change `role-master/cluster/admin*.sls` to `role-master/cluster/$NAME_OF_YOUR_ADMIN_NODE*.sls`

If you need more detailed information please refer to the [Policy wiki page](https://github.com/SUSE/DeepSea/wiki/policy).

If you need to change the cluster's network setting, edit `/srv/pillar/ceph/proposals/config/stack/default/ceph/cluster.yml` and adjust the lines starting with `cluster_network:` and `public_network:`

#### Stage 2
The configuration stage parses the policy.cfg file and merges the included files into their final form. Cluster and role related contents are placed in `/srv/pillar/ceph/cluster`, 
while Ceph specific content is placed in `/srv/pillar/ceph/stack/default`.

Run the following command to trigger the configuration stage:
- `salt-run state.orch ceph.stage.2`or `salt-run state.orch ceph.stage.configure`

The configuration step may take several seconds. After the command finishes, you can view the pillar data for the specified minions (for example named ceph_minion1, ceph_minion2 ...) by running:
- `salt 'ceph_minion*' pillar.items`

#### Stage 3
Now you run the deployment stage. In this stage, the pillar is validated and monitors and ODS daemons are started on the storage nodes. Run the following to start the stage:
- `salt-run state.orch ceph.stage.3` or `salt-run state.orch ceph.stage.deploy`

The command may take several minutes. If it fails, you have to fix the issue and run the previous stages again. After the command succeeds, run the following to check the status:

- `ceph -s`

If you only want to deploy a Ceph cluster without any additional services, congratulations - you're done. Otherwise you have to continue with Stage 4.

#### Stage 4
The last step of the Ceph cluster deployment is the services stage. Here you instantiate any of the currently supported services: iSCSI Gateway, CephFS, RADOS Gateway, openATTIC, and NFS Ganesha. 
In this stage, the necessary pools, authorizing keyrings and starting services are created. To start the stage, run the following:

- `salt-run state.orch ceph.stage.4` or `salt-run state.orch ceph.stage.services`

Depending on the setup, the command may run several minutes. If you specified the openATTIC role it will be installed on the master node by default. If you need to install openATTIC on a different node, please take a look at the upstream [openATTIC documentation](http://docs.openattic.org/en/latest/install_guides/). If you do not need to install openATTIC at all remove the role from your policy.cfg.

## Test intial deployment and generating load
Once a cluster is deployed one might want to verify functionality or run
benchmarks to verify the cluster works as expected.

In order to gain some confidence in your cluster after the inital deployment
(stage 3) run: 

- `salt-run state.orch ceph.benchmarks.baseline`. 

This runs an osd benchmark on each OSD and aggregates the results. It reports your average OSD performance and points out OSDs that deviate from the average. *Please note 
that for now the baseline benchmark assumes all uniform OSDs.*

To load test CephFS run:

- `salt-run state.orch ceph.benchmarks.cephfs`.

This requires a running MDS (deploy in stage 4) and at least on minion with the mds-client role. The cephfs_benchmark stage will then mount the CephFS 
instance on the mds-client and run a bunch of fio tests. See the [benchmark readme](srv/pillar/ceph/benchmark/README.md) for futher details.
