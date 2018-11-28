[![Build Status](https://travis-ci.org/SUSE/DeepSea.svg?branch=master)](https://travis-ci.org/SUSE/DeepSea)
# DeepSea
A collection of [Salt](https://saltstack.com/salt-open-source/) files for deploying, managing and automating [Ceph](https://ceph.com/).

The goal is to manage multiple Ceph clusters with a single salt master. At this time, only a single Ceph cluster can be managed.

This [diagram](deepsea.png) should explain the intended flow for the orchestration runners and related salt states.

## Status
DeepSea currently supports the following functionality:

- Automatic discovery, deployment, configuration and life cycle management of Ceph clusters
- Initial support for importing Ceph clusters deployed by other tools, e.g. using `ceph-deploy`
- RADOS Gateway deployment (for single site deployments)
- CephFS MDS deployment and CephFS creation
- Sharing CephFS or S3 buckets via [NFS Ganesha](http://nfs-ganesha.github.io/)
- iSCSI target management via [lrbd](https://github.com/SUSE/lrbd/)
- Deployment and configuration of [Prometheus](https://prometheus.io/) and [Grafana](https://grafana.com/) for monitoring / performance data visualization

## Get Involved
To learn more about DeepSea, take a look at the [Wiki](https://github.com/SUSE/DeepSea/wiki).

There is also a dedicated mailing list [deepsea-users](http://lists.suse.com/mailman/listinfo/deepsea-users).
If you have any questions, suggestions for improvements or any other
feedback, please join us there! We look forward to your contribution.

If you think you've found a bug or would like to suggest an enhancement, please submit it via the [bug tracker](https://github.com/SUSE/DeepSea/issues/new) on GitHub.

If you would like to contribute to DeepSea, refer to the [contribution guidelines](https://github.com/suse/deepsea/blob/master/contributing.md).

## Developers and Admins
For those interested in learning about some of the uses of Salt in DeepSea, see [here](https://github.com/suse/deepsea/blob/master/salt.md) for explanations and examples.
 
## Usage
You need at least a minimum of 4 nodes to be able to test and use DeepSea properly.

[Developer setups that can spawn and provision VMs for you.](#developer-setups)

To be able to use less than 4 nodes during the deployment stages (e.g. in a
development/testing environment), you could set the option `DEV_ENV=true` as an
environment variable or globally as a pillar variable in
`/srv/pillar/ceph/stack/global.yml`. Setting `DEV_ENV` allows you to:

- Deploy monitors without the presence of a `profile` directory
- Deply a cluster with at least _one_ (instead of 3/4/3) storage/monitor/mgr
  nodes

## Developer Setups

There are a couple of ways to spawn and provision VMs, but most people currently use
a `Vagrant` based solution called [vagrant-ceph](https://github.com/opensuse/vagrant-ceph)

There is also a terraform based solution called [ceph-open-terrarium](https://github.com/mallozup/ceph-open-terrarium)


### Add DeepSea repo to your admin host

DeepSea needs to be installed on the Salt master node.

On openSUSE distributions, this step could be performed by installing the RPM package [from the openSUSE build service](https://build.opensuse.org/package/show/filesystems:ceph:luminous/deepsea), following the [installation instructions](https://software.opensuse.org//download.html?project=filesystems%3Aceph%3Aluminous&package=deepsea).

On other distributions or when using a development version, install Salt via the
distribution's preferred installation method and check out the git repository:

```
$ git clone https://github.com/SUSE/DeepSea.git
$ cd DeepSea
$ sudo make install
```

### Cluster Preparation 
The cluster deployment process has several phases. First, you need to prepare all nodes of the cluster by configuring Salt and then deploy and configure Ceph.

The following procedure describes the cluster preparation in detail.

Install a minimum of four machines (or define `DEV_ENV=true` either as an environment variable or a pillar variable during the deployment process) with SUSE Leap 42.3 or Tumbleweed and add the DeepSea repo to your defined "admin" node:

```
# zypper ar http://download.opensuse.org/repositories/filesystems:/ceph:/luminous/openSUSE_Leap_42.3/filesystems:ceph:luminous.repo
# zypper refresh
```

Make sure that each node can resolve the host names of all other nodes. 

The Salt master needs to resolve all its Salt minions by their host names, as well as all Salt minions need to resolve the Salt master by its host name. 

If you don't have a DNS Server you could also add all hosts of your cluster to the ``/etc/hosts``` file. 

Configure, enable, and start the NTP time synchronization server on all nodes:

```
# systemctl enable ntpd.service
# systemctl start ntpd.service
```

Note that the Cluster deployment with DeepSea will not work with Firewall/AppArmor enabled.

Check whether the AppArmor service is running and disable it on each cluster node to avoid problems:

```
# systemctl disable apparmor.service
```

Check whether the Firewall service is running and disable it on each cluster node to avoid problems:

```
# systemctl disable SuSEfirewall2.service
```

Install DeepSea on the node which will be the Salt master:

```
# zypper install deepsea
```

The command installs the `salt-master` and `salt-minion` packages as a dependency.

Check that the `salt-master` service is enabled and started - enable and start it if needed:

```
# systemctl enable salt-master.service
# systemctl start salt-master.service
```

Install the package `salt-minion` on all minion nodes:

```
# zypper in salt-minion
```

Configure all minions (including the master minion) to connect to the master. If
your Salt master is not reachable by the host name "salt", edit the file
`/etc/salt/minion` or create a new file `/etc/salt/minion.d/master.conf` with
the following content:

```
master: host_name_of_salt_master
```

If you performed any changes to the configuration files mentioned above, restart
the Salt service on all Salt minions:

```
# systemctl restart salt-minion.service
```

Check that the file `/srv/pillar/ceph/master_minion.sls` on the Salt master
points to your Salt master.

If your Salt master is reachable via more host names, use the one suitable for
the storage cluster. If you used the default host name for your Salt master in
the example domain, then the file looks as follows:

```
master_minion: salt.example
```

Check that the `salt-minion` service is enabled and started on all nodes (including
the master node). Enable and start it if needed:

```
# systemctl enable salt-minion.service`
# systemctl start salt-minion.service
```

Accept all salt keys on the Salt master:
```
# salt-key --accept-all
```

Verify that the keys have been accepted:

```
# salt-key --list-all
```
In order to avoid conflicts with other minions managed by the Salt master, DeepSea
needs to know which Salt minions should be considered part of the Ceph cluster to
be deployed. This can be configured in file `/srv/pillar/ceph/deepsea_minions.sls`,
by defining a naming pattern. By default, DeepSea targets all minions that have a
grain `deepsea` applied to them. This can be accomplished by running the following
Salt command on all Minions that should be part of your Ceph cluster:

```
# salt -L <list of minions> grains.append deepsea default
````

Alternatively, you can change `deepsea_minions` in `deepsea_minions.sls` to any valid
Salt target definition. See `man deepsea-minions` for details.

#### Cleanup your Disks - only needed if your disks were used in a cluster before

Prior to deploying a cluster with DeepSea make sure that all disks that were
used as OSD by previous clusters are empty without partitions. To ensure this,
you have to manually zap all the disks. Remember to replace 'X' with the correct
disk letter.

**Attention** - *This command will remove all your data from that disk, please
be careful!*

Wipe the beginning of each partition:

```
# for partition in /dev/sdX[0-9] ; do \
dd if=/dev/zero of=$partition bs=4096 count=1 oflag=direct ; done
```

Wipe the partition table:

```
# sgdisk -Z --clear -g /dev/sdX
```

Wipe the backup partition tables:

```
# size=`blockdev --getsz /dev/sdX`
# position=$((size/4096 - 33))
# dd if=/dev/zero of=/dev/sdX bs=4096 count=33 seek=$position oflag=direct
```

Now you deploy and configure Ceph. Unless specified otherwise, all steps are
mandatory.

**Note: Salt Command Conventions**

There are two possibilities how to run `salt-run state.orch` - one is with
`stage.<stage number>`, the other is with a name of the stage. Both notations
have the same impact and it is fully up to your preference which command you
want to use. Both notations are used in the following deployment steps. So
please choose what you prefer.

### Cluster Deployment

#### Stage 0
During this stage all required updates are applied and your system may be
rebooted.

```
salt-run state.orch ceph.stage.0
```

or

```
salt-run state.orch ceph.stage.prep
```

Note: If during Stage 0 the Salt master reboots to load new kernel version, you
need to run Stage 0 again, otherwise minions will not be targeted.

#### Stage 1
The discovery stage collects all hardware in your cluster and also collects
necessary information for the Ceph configuration. The configuration fragments
are stored in the directory `/srv/pillar/ceph/proposals`. 

The data is stored in YAML format in `*.sls` or `*.yml` files.

```
salt-run state.orch ceph.stage.1
```
or
```
salt-run state.orch ceph.stage.discovery
```

After the previous command finishes successfully, create a `policy.cfg` file in
`/srv/pillar/ceph/proposals`.

You can find an example in our
[docs](https://github.com/SUSE/DeepSea/blob/master/doc/examples/policy.cfg-rolebased)
folder. Please change the example file to fit to your needs, e.g. by changing
`role-master/cluster/admin*.sls` to
`role-master/cluster/$NAME_OF_YOUR_ADMIN_NODE*.sls`

If you need more detailed information please refer to the [Policy wiki
page](https://github.com/SUSE/DeepSea/wiki/policy).

If you need to change the cluster's network setting, edit
`/srv/pillar/ceph/proposals/config/stack/default/ceph/cluster.yml` and adjust
the lines starting with `cluster_network:` and `public_network:`.

#### Stage 2
The configuration stage parses the `policy.cfg` file and merges the included files
into their final form. Cluster and role related contents are placed in
`/srv/pillar/ceph/cluster`, while Ceph specific content is placed in
`/srv/pillar/ceph/stack/default`.

Run the following command to trigger the configuration stage:

```
# salt-run state.orch ceph.stage.2
```
or
```
# salt-run state.orch ceph.stage.configure
```

The configuration step may take several seconds. After the command finishes, you
can view the pillar data for the specified minions (for example named
`ceph_minion1`, `ceph_minion2` ...) by running:

```
# salt 'ceph_minion*' pillar.items
```

#### Stage 3
Now you run the deployment stage. In this stage, the pillar is validated and monitors and ODS daemons are started on the storage nodes. Run the following to start the stage:

```
# salt-run state.orch ceph.stage.3
```
or
```
# salt-run state.orch ceph.stage.deploy
```

The command may take several minutes. If it fails, you have to fix the issue and run the previous stages again. After the command succeeds, run the following to check the status:

```
# ceph -s
```

If you only want to deploy a Ceph cluster without any additional services,
congratulations - you're done. Otherwise you have to continue with Stage 4.

#### Stage 4
The last step of the Ceph cluster deployment is the services stage. Here you
instantiate any of the currently supported services: iSCSI Gateway, CephFS,
RADOS Gateway, and NFS Ganesha. In this stage, the necessary pools,
authorizing keyrings and starting services are created.

To start the stage, run the following:

```
# salt-run state.orch ceph.stage.4
```
or

```
salt-run state.orch ceph.stage.services
```

## Test intial deployment and generating load
Once a cluster is deployed one might want to verify functionality or run
benchmarks to verify the cluster works as expected.

In order to gain some confidence in your cluster after the inital deployment
(stage 3) run: 

```
# salt-run state.orch ceph.benchmarks.baseline
``` 

This runs an osd benchmark on each OSD and aggregates the results. It reports
your average OSD performance and points out OSDs that deviate from the average. 

*Please note that for now the baseline benchmark assumes all uniform OSDs.*

To load test CephFS run:

```
# salt-run state.orch ceph.benchmarks.cephfs
```

This requires a running MDS (deploy in stage 4) and at least on minion with the
`client-cephfs` role. The `cephfs_benchmark` stage will then mount the CephFS
instance on the mds-client and run a bunch of `fio` tests. See the [benchmark
readme](srv/pillar/ceph/benchmarks/README.md) for further details.

```
# salt-run state.orch ceph.benchmarks.rbd
```

This runs fio using the RBD backend against the cluster as a whole. This
requires at least one minion with the `benchmark-rbd` role. See the
[benchmark readme](srv/pillar/ceph/benchmarks/README.md) for further details.

