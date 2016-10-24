# Management

Installing and modifying a Ceph cluster are no different in DeepSea.  

## Prerequisites

The prerequisites are

* a working Salt cluster

* DeepSea installed

* access to Ceph Jewel repositories or later

*One caveat at the moment is that DeepSea contains two SUSE-isms.  One is the module cephdisks.py contains a call to **hwinfo**.  The other is the references to the **zypper** command directly. These will be addressed.*

## Command Convention

Each of the stages can be called with either the descriptive name or the number.  For example, these two commands are equivalent.

`# salt-run state.orchestrate ceph.stage.prep`

`# salt-run state.orch ceph.stage.0`

The actual location of the orchestartion file is in /srv/salt/ceph/stage/prep.  The init.sls redirects to default.sls unless overridden.  

The instructions will use the short form, but feel free to use either.

## Manual Installation

### Prep

The first stage is to apply updates to all servers, also known as minions.  Run the following:

```
# salt-run state.orch ceph.stage.0
```

This stage normally takes some time on the initial update.  The master updates first and then the remaining minions update in parallel.  If an update changes the kernel, the server will reboot to use the new kernel.  With no automation, run the command a second time to complete this stage.

### Discovery

The next stage collects the interesting data from all the minions and creates configuration fragments.  These are stored in subdirectories under /srv/pillar/ceph/proposals.  

The subdirectories are structured to be convenient for the Salt external pillar.  In several of the directories are text files with either sls or yml extensions.  All contain YAML formatted data.

To create these directories and files, run

```
# salt-run state.orch ceph.stage.1
```

This stage takes a few seconds.  Once complete, create a policy.cfg file in /srv/pilar/ceph/proposals.  For detailed information, see the [policy](policy) instructions.

### Configure

This stage parses the policy.cfg and merges the selected files into their final form.  Cluster and role related contents are placed in /srv/pillar/ceph/cluster.  The Ceph specific content is placed in /srv/pillar/ceph/stack/default.  

To add the content to the Salt pillar, run

```
# salt-run state.orch ceph.stage.2
```

This may take several seconds.  Once complete, view the pillar data for all minions with
 
```
# salt '*' pillar.items
```

### Overriding the Configuration

Examine the output.  If any data is incorrect for your environment, override it now.  For instance, if the guessed cluster network is `10.0.1.0/24`, but the preferred cluster network is `172.16.22.0/24`, do the following:

* Edit the file /srv/pillar/ceph/cluster.yml

* Add `cluster_network: 172.16.22.0/24`

* Save the file

To verify the change, run

```
# salt '*' saltutil.pillar_refresh
# salt '*' pillar.items
```

This can be repeated with any configuration data.  For examples, examine any of the files under /srv/pillar/ceph/stack/default which contains a duplicate directory tree.

### Deploy

This stage validates the pillar, create the monitors and osds on the storage nodes.  If the validation fails, correct the issue.  The correction may require rerunning the previous stages.

To create the core Ceph cluster, run

```
# salt-run state.orch ceph.stage.3
```

This command will take a few minutes, but possibly longer depending on the number of drives on the storage node.  Once complete, run

```
# ceph -s
```

### Services

This stage will instantiate any roles outside of the basic cluster.  The current services are iSCSI, CephFS, RadosGW and openATTIC.  This includes creating the necessary pools, authorizing keyrings and starting services.

To add services, run 

```
# salt-run state.orch ceph.stage.4
```

Depending on the services assigned, this stage may take a few minutes.

### Removal

This stage will rescind roles and remove any other cluster configuration.  During an initial setup, this step is not truly necessary.  However, running this stage will not harm your cluster.

To remove roles from minions, run

```
# salt-run state.orch ceph.stage.5
```

This stage will normally take several seconds.  The notable exception is when a storage node is decommisioned.  The OSDs gracefully empty before completing their removal.  Between cluster activity, available network bandwidth and the number of PGs to migrate, this operation can take considerably longer.

## Automated Installation

The installation can be automated by using the Salt reactor.  For virtual environments or consistent hardware environments, this configuration will allow the creation of a Ceph cluster with the specified behavior.

The prerequisites are the same as the manual installation.  The policy.cfg must be created beforehand and placed in /srv/pillar/ceph/proposals.  Any custom configurations may also be placed in /srv/pillar/ceph/stack in their appropriate files before starting the stages.

*Note to self.. rearrange file locations in spec*

Finally, copy the example reactor file from /usr/share/doc/packages/deepsea/reactor.conf to /etc/salt/master.d/reactor.conf.  

The default reactor configuration will only run Stages 0 and 1.  This allows testing of the reactor without waiting for subsequent stages to complete.

When the first salt-minion starts, Stage 0 will begin.  A lock prevents multiple instances.  When all minions complete Stage 0, Stage 1 will begin.

When satisfied with the operation, change the last line in the reactor.conf
from 

`   - /srv/salt/ceph/reactor/discovery.sls`

to

`   - /srv/salt/ceph/reactor/all_stages.sls`

### Caution

Experimentation with the reactor is known to cause frustration.  Salt cannot perform dependency checks based on reactor events.  Putting your Salt master into a death spiral is a real risk.

## Reinstallation

When a role is removed from a minion, the objective is to undo all changes related to that role.  For most roles, this is simple.  An exception relates to package dependencies.  When a package is uninstalled, the dependencies are not.  

With regards to storage nodes, a removed OSD will appear as blank drive.  The related tasks overwrite the beginning of the filesystems and remove backup partitions in addition to wiping the partition tables.  

Disk drives previously configured by other methods, such as ceph-deploy, may still contain partitions.  DeepSea will not automatically destroy these.  Currently, the administrator must reclaim these drives.

