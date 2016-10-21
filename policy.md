# Policy

The selection for all assignments resides in a single file.  The file is /srv/pillar/ceph/proposals/policy.cfg.

## Interfaces

At this time, only directly creating or copying an example and editing is available.  Other solutions are in development to simplify this process for newcomers.

## Purpose

The Salt configuration data or Salt pillar allows for data to be shared with all minions, specific groups of minions or individual minions.  The organization of this data is left to the administrator to decide.  A single configuration file may be suitable for some purposes, but does not provide granularity that Salt accommodates.

While some of the data for a Ceph cluster would not be difficult to maintain manually, specifically the cluster and role assignment, other data such as device names paths for every OSD would be impractical.  Salt can provide all of this information and save the administrator manual effort.

Salt cannot know which minions are to perform which roles nor which to include in the Ceph cluster at all.  The administrator needs a method to dictate these wishes.  The policy.cfg fulfills this purpose.

## Format

The policy.cfg has a single function, which is to include other files.  The pathnames are relative.  Comments are permitted.  Shell globbing is the simplest form for matching files.  

The provided examples divide the file into four commented sections: Cluster assignment, Role assignment, Common configuration and Profile assignment.  The order of these sections is arbitrary, but the contents of included lines will overwrite matching keys from the contents of previous lines.  Lists and dictionaries will be combined.

All the lines containing *cluster* will have an sls extension.  All lines containing *stack* will have a yml extension.  Both contain YAML.  The sls files are technically Salt files and placed directly into the Salt pillar.  The yml files are placed in a separate subdirectory and accessed by an external pillar called stack.py.  The contents of the sls files influence the selection of the yml files.  For further information, consult the /srv/pillar/ceph/stack/stack.cfg.

## Cluster Assignment

A Salt cluster contains minions.  Any may be selected to use for a Ceph cluster.  To select all minions for the cluster named **ceph**, add the following

```
cluster-ceph/cluster/*.sls
```

Depending on the ratio of minions included in your cluster, white listing or black listing may be preferred.  Both are supported.

For white listing, simply include the minion file or matching shell glob.  For example,

```
cluster-ceph/cluster/abc.domain.sls
cluster-ceph/cluster/mon*.sls
```

For black listing, set the minions to *unassigned* to exclude them from the cluster.

```
cluster-ceph/cluster/*.sls
cluster-unassigned/cluster/client*.sls
```

## Role Assignment

The basic roles are master, admin, mon, mds, igw and rgw.  Storage is covered in Profile Assignment.  To assign any of these roles to minions, add a line matching the desired minions.

```
role-mon/cluster/mon*.sls
```

Shell globbing allows more specific matching and a single minion may have multiple roles.  For instance, two monitor nodes may also provide mds with the following

```
role-mds/cluster/mon[12]*.sls
```

### master

The master role will have the admin keyrings to all Ceph clusters.  Currently, only a single Ceph cluster is supported.  

### admin

The admin role determines which minions get an admin keyring.  

### mon

The mon role provides the monitor service for the Ceph cluster.

### mds

The mds role provides the metadata services to support CephFS.

### igw

The igw role configures minions to be iSCSI gateways.

### rgw

The rgw role configures minions to be RadosGW gateways.

### Special cases: mon and igw

These two roles require addresses of the assigned minions to complete their configuration.  These files are already present, but must be included.  Use the same glob matching for role assignment, but specify the minion files in the stack directory.  For instance

```
role-mon/stack/default/ceph/minions/mon*.yml
role-igw/stack/default/ceph/minions/xyz.domain.yml
```

## Profile Assignment

In Ceph, a single storage role would be insufficient to describe the many disk configurations available with the same hardware.  Therefore, stage 1 will generate multiple profiles when possible for the same storage node.  The administrator adds the *cluster* and *stack* related lines similar to the mon and igw roles.  

The directory names begin with *profile-* and end with a single digit.  The label is dynamically generated based on the quantity, model and size of the media.  Examples are 2Disk2GB and 3HP5588GB.  The final directory would be profile-2Disk2GB-1 or profile-3HP5588GB-1.  

The digit after the final hyphen represents one possible profile.  With any storage node, one configuration is to treat all disk media as individual OSDs.  All **-1** configurations will be this configuration.  

To select a specific profile for a storage node, add the two lines matching the desired profile.  For example,

```
profile-2Disk2GB-1/cluster/data*.sls
profile-2Disk2GB-1/stack/default/ceph/minions/data*.yml
```

or

```
profile-3HP5588-1/cluster/*.sls
profile-3HP5588-1/stack/default/ceph/minions/*.yml
```

If a storage node contains solid state media (e.g. SSD or NVMe), then other configurations are considered using the solid state media as separate journals.  Depending on the number of models and ratio of drives, additional profiles may be created.  These new profiles increment the last digit.

```
profile-2Intel745GB-6INTEL372GB-2/cluster/*.sls
profile-2Intel745GB-6INTEL372GB-2/stack/default/ceph/minions/*.yml
```

*At this time, the administrator must examine the contents of the yml file in the stack/default/ceph/minions directory to see the configuration.*

With a mix of hardware, multiple combinations are possible.  Add as many lines as needed to select a single profile for each storage node.  For instance,

```
profile-24HP5588-1/cluster/cold*.sls
profile-24HP5588-1/stack/default/ceph/minions/cold*.yml
profile-18HP5588-6INTEL372GB-2/cluster/data*.sls
profile-18HP5588-6INTEL372GB-2/stack/default/ceph/minions/data*.yml
```
 
## Common Configuration

Ceph requires certain parameters such as an fsid or public_network.  Stage 1 will generate default values.  To include these, add the following lines

```
config/stack/default/global.yml
config/stack/default/ceph/cluster.yml
```

## File Matching

Shell globbing is most useful for minions dedicated to a single role.  The example file is policy.cfg-rolebased.

With cloud environments, the hostnames may change from setup to setup and not be known in advance.  A slice parameter 

