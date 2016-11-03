# Intro

A brief summary of DeepSea, why it exists and how it is organized follows.

## What is DeepSea?

DeepSea is a collection of Salt states, runners and modules for deploying and managing Ceph.  For more information about Salt, see https://docs.saltstack.com/en/latest/.  For more information about Ceph, see http://docs.ceph.com/docs/master/.

The traditional method for deploying Ceph is ceph-deploy http://docs.ceph.com/docs/master/man/8/ceph-deploy/.  As the page says, ceph-deploy has low overhead but that overhead is passed on to the administrator.  For a distributed storage system, a configuration management/automation framework is essential.  Salt is fast, allows manual execution of commands on remote systems and provides many components for automating complex configurations.

## Philosophy

The goal of DeepSea is to save the administrator time and confidently perform complex operations on a Ceph cluster.  This idea has driven a few choices.  Before presenting those choices, some observations are necessary.

All software has configuraton.  Sometimes the default is sufficient.  This is not the case with Ceph.  Ceph is flexible almost to a fault.  Reducing this complexity would force administrators into preconceived configurations.  Several of the existing Ceph solutions for an installation create a demonstration cluster of three nodes.  However, the most interesting features of Ceph require more.  

One aspect of configuration management tools is accessing the data such as addresses and device names of the individual servers.  For a distributed storage system such as Ceph, that aggregate can run into the hundreds.  Collecting the information and entering the data manually into a configuration management tool is prohibitive and error prone.

The steps necessary to provision the servers, collect the configuration, configure and deploy Ceph are mostly the same.  However, this does not address managing the separate functions.  For day to day operations, the ability to trivially add hardware to a given function and remove it gracefully is a requirement.

With these observations in mind, DeepSea addresses them with the following strategy:

Collect each set of tasks into a simple goal.  Each goal is a Stage.  DeepSea currently has six stages described below.

* **Stage 0 Provisioning**
While many sites will provide their own provisioning of servers, the various virtual and cloud environments may not.  This stage is optional but present to allow for updating and rebooting if necessary.

* **Stage 1 Discovery**
Considering the wide range of supported hardware by Ceph, use Salt to interrogate each of the servers and collect the necessary information for configuring Ceph.

* **Stage 2 Configure**
Since Salt is the mechanism for configuring, deploying and managing Ceph, Salt requires this configuration data in a particular format.  

* **Stage 3 Deploy**
Create the basic Ceph system consisting of monitors and storage nodes.

* **Stage 4 Services**
Configure the additional features of Ceph such as iSCSI, RadosGW and CephFS.  Each is optional.

* **Stage 5 Removal**
When hardware fails or is retired, remove the assigned functions and update the Ceph cluster accordingly.

Consolidate the administrator's decisions in a single location.  The decisions revolve around cluster assignment, role assignment and profile assignment.

* **Cluster assignment**
Decide whether all servers in the Salt cluster are available for the Ceph cluster.

* **Role assignment**
Decide whether a server has a dedicated role or many roles.

* **Profile assignment**
Decide which OSD configuration should be assigned to a storage node.

Essentially, that is all there is to DeepSea.  DeepSea uses Stages to implement the decisions of the administrator to create and modify a Ceph cluster.

## Salt

For those completely unfamiliar with Salt, think of the use of Salt as a collection of modularized shell scripts with colorful output.  Another noteworthy behavior is that Salt is asynchronous in the common case.  In other words, running many Salt commands is similar to backgrounding a process although the command line client will wait for a response.  Some admins will find this initially unsettling.
 
Salt has standard locations and some naming conventions.  The configuration data for your Salt cluster is kept in /srv/pillar.  The files representing the various tasks are called state files or sls files.  These are kept in /srv/salt.  

Two other important locations are /srv/module/runners and /srv/salt/_modules.  The former holds python scripts known as runners.  These run in a particular context on the Salt master.  The latter are user defined modules.  These modules are also python scripts but the return values are important.  Also, the modules only run on the minions.  The minion is the daemon or agent that carries out the tasks from the master.

## Organization

In an effort to separate namespaces, DeepSea uses /srv/pillar/ceph and /srv/salt/ceph.  The discovery stage stores the collected configuration data in a subdirectory under /srv/pillar/ceph. The configure stage aggregates this data according to the wishes of the admin and stores the result in an external pillar.  The data is now available for Salt commands and processes.

The Salt commands use the files stored in the various subdirectories in /srv/salt/ceph.  Although all the files have an sls extension, the formats differ.  To prevent confusion, all sls files in a subdirectory are of one kind.  For example, /srv/salt/ceph/stage contains orchestration files that are executed by the **salt-run state.orchestrate** command.  Another example is /srv/salt/ceph/admin.  These files are executed by the **salt** *target* **state.apply** command.  Most subdirectories follow the latter example.

