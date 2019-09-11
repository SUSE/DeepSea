# DeepSea
A collection of [Salt](https://saltstack.com/salt-open-source/) files for deploying, managing and automating [Ceph](https://ceph.com/).

The goal is to manage a Ceph cluster with a single salt master.

![deepsea mascot](https://raw.githubusercontent.com/SUSE/DeepSea/master/doc/mascot/mascot.png)

## Status
DeepSea currently supports the following functionality:

- Automatic discovery, deployment, configuration and life cycle management of Ceph clusters
- RADOS Gateway deployment
- CephFS MDS deployment and CephFS creation
- Sharing CephFS or S3 buckets via [NFS Ganesha](http://nfs-ganesha.github.io/)
- iSCSI target management via ceph-iscsi [ceph-iscsi](https://github.com/ceph/ceph-iscsi)
- Deployment and configuration of [Prometheus](https://prometheus.io/) and [Grafana](https://grafana.com/) for monitoring / performance data visualization

## Get Involved
To learn more about DeepSea, take a look at the [Wiki](https://github.com/SUSE/DeepSea/wiki). [deprecated TODO!]

There is also a dedicated mailing list [deepsea-users](http://lists.suse.com/mailman/listinfo/deepsea-users).
If you have any questions, suggestions for improvements or any other
feedback, please join us there! We look forward to your contribution.

If you think you've found a bug or would like to suggest an enhancement, please submit it via the [bug tracker](https://github.com/SUSE/DeepSea/issues/new) on GitHub.

If you would like to contribute to DeepSea, refer to the [contribution guidelines](https://github.com/suse/deepsea/blob/master/contributing.md).

## Developers and Admins
For those interested in learning about some of the uses of Salt in DeepSea, see [here](https://github.com/suse/deepsea/blob/master/salt.md) for explanations and examples.

## Usage

You need at least a minimum of 4 nodes to be able to test and use DeepSea properly.

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

Make sure that each node can resolve the host names of all other nodes.

The Salt master needs to resolve all its Salt minions by their host names, as well as all Salt minions need to resolve the Salt master by its host name.

If you don't have a DNS Server you could also add all hosts of your cluster to the ``/etc/hosts``` file.

Configure, enable, and start the NTP time synchronization server on all nodes:

```
# systemctl enable ntpd.service
# systemctl start ntpd.service
```

Check whether the Firewall service is running and disable it on each cluster node to avoid problems:

The following commands are tailored to openSUSE/SUSE. Please use the corresponding commands for your distribution.

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


DeepSea uses podman to deploy Ceph on the minions. Please make sure to have
podman installed on your nodes.

For openSUSE 15.1 you want to add this [repository](https://build.opensuse.org/package/show/openSUSE:Leap:15.1:Update/podman])

DeepSea will try to fetch a container image specified in the internals.yml. Please edit this file and adapt this path to
a container image of your choice (TODO: we may point to a official image from opensuse once this is released)

### Cluster Deployment

Initially you want to get a minimal working cluster up and running. For this you execute the bootstrap runner.


```
salt-run bootstrap.ceph
```

This command will interactively guide you through a dialogue. There is also a non-interactive mode for situations where
you already know your requirements.

You can pass it like so:


```
salt-run bootstrap.ceph non_interactive=True
```

This will bring up a cluster with *one* ceph-monitor(mon) and *one* ceph-manager(mgr).
From now on we'll use the abbreviations for these services. You can read more about these [here](https://docs.ceph.com/docs/master/start/intro/)

Please follow the instructions of the bootstrap runner.


### Interface:

All ceph-components (ceph-mgr, ceph-mon etc) are depicted in a so-called 'salt-runner'.

They are designed to have a consistent interface.

The minimal set of operations are:

* deploy
* remove
* update

These can be invoked using the 'dot' notaion with a prepended `salt-run` indication that it's run with the salt context.

For the ceph-monitors it will look like this:

```
salt-run mon.deploy

salt-run mon.remove

salt-run mon.update

```

ceph-managers(mgr) would be invoked like so:

```
salt-run mgr.deploy

salt-run mgr.remove

salt-run mgr.update

```
