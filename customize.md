# Customize

Administrators may wish to customize certain steps which is similar to overriding the default steps.

## Disabling a Step

Some sites address problems differently.  If a step is addressed outside the scope of Salt, do the following

* Create a no op file.  For example, to disable time synchronization, create /srv/salt/ceph/time/disabled.sls.  Enter the following:

```
disable time setting:
  test.nop
```
* Save the file

* Edit /srv/pillar/ceph/stack/global.yml

* Add `time_init: disabled`

* Save the file

Verify by refreshing the pillar and running the step.

```
# salt '*' saltutil.pillar_refresh
# salt 'admin.ceph' state.apply ceph.time
```

The output will be

```
admin.ceph:
  Name: disable time setting - Function: test.nop - Result: Clean

Summary for admin.ceph
------------
Succeeded: 1
Failed:    0
------------
Total states run:     1
```

Note that the ID *disable time setting* could be any message but an ID must be unique within an sls file.  Prevent ID collisions by specifying unique descriptions.

## Replacing a Step

The behavior of /srv/salt/ceph/pool/default.sls creates an rbd image called *demo*.  Instead the administrator wants two images: *archive* and *archive1*. To replace this step, do the following:

* Create /srv/salt/ceph/pool/custom.sls  Enter the following:

```
wait:
  module.run:
    - name: wait.out
    - kwargs:
        'status': "HEALTH_ERR"
    - fire_event: True

archive:
  cmd.run:
    - name: "rbd -p rbd create archive --size=1024"
    - unless: "rbd -p rbd ls | grep -q archive$"
    - fire_event: True

archive1:
  cmd.run:
    - name: "rbd -p rbd create archive1 --size=768"
    - unless: "rbd -p rbd ls | grep -q archive1$"
    - fire_event: True

```

* Save the file

The wait module will pause until the Ceph cluster does not have a status of HEALTH_ERR.  In fresh installations, a Ceph cluster may have this status until a sufficient number of OSDs become available and creation of pools has completed.

The **rbd** command is not idempotent.  If the same creation command is rerun afer the image exists, the salt state will fail.  The unless statement prevents this.

To call this custom file instead of the default, do the following:

* Edit /srv/pillar/ceph/stack/ceph/cluster.yml

* Add `pool_init: custom`

* Save the file


Verify by refreshing the pillar and running the step.

```
# salt '*' saltutil.pillar_refresh
# salt 'admin.ceph' state.apply ceph.pool
```

Note that the creation of pools or images requires sufficient authorization.  The *admin.ceph* minion has an admin keyring.

Another option is to change the variable in /srv/pillar/ceph/stack/ceph/roles/master.yml instead.  Using this file will reduce the clutter of pillar data for other minions.

## Modifying a Step

Sometimes the administrator needs a specific step to do something extra.  The recommendation is against directly modifying the state file which may complicate a future upgrade.

Instead, create a seperate file to carry out the additional tasks identical to [Replacing a Step](Replacing a Step).  Name the file something descriptive.  For example, if the administrator wants the two rbd images in addition to the demo image, name the file archive.sls.  Next,

* Create /srv/salt/ceph/pool/custom.sls.  Enter the following:

```
include:
  - .archive
  - .default
```
* Save the file

Perform the same steps as before.

* Edit /srv/pillar/ceph/stack/ceph/cluster.yml

* Add `pool_init: custom`

* Save the file

Verify by refreshing the pillar and running the step.

```
# salt '*' saltutil.pillar_refresh
# salt 'admin.ceph' state.apply ceph.pool
```

### Salt Include Precedence

In this example, Salt will create the archive images and then create the demo image.  The order does not matter in this example.  To change the order, reverse the lines.

Some may notice that the include line could simply be added directly to archive.sls and all the images would get created.  However, regardless of where the include line is placed, Salt processes the steps in the included file first.  Although this behavior can be overridden with requires and order statements, a separate file that includes the others guarantees the order and reduces the chances of confusion.

## Modifying a Stage

An administrator may want to add a completely separate step.  For instance, the admin would like to run logrotate on all minions as part of the provisioning stage.  (This is a contrived example and may be more useful to a developer than an administrator, but the process is the same.)

Since the goal is to run a task on a set of minions, different files are necessary.  One is the state sls file that performs the logrotate command.  Do the following:

* Create a directory, perhaps /srv/salt/ceph/custom or /srv/salt/ceph/logrotate.  This example will use the latter.

* Create /srv/salt/ceph/logrotate/init.sls.  Enter the following:

```
rotate logs:
  cmd.run:
    - name: "/usr/sbin/logrotate /etc/logrotate.conf"
```
Verify that the command works on a minion.

```
# salt 'admin.ceph' state.apply ceph.logrotate
```

The second file is an orchestration file.  Since this should run before all other provisioning steps, add this file to the Prep stage also known as Stage 0.  Do the following:

* Create /srv/salt/ceph/stage/prep/logrotate.sls.  Enter the following:

```
logrotate:
  salt.state:
    - tgt: '*'
    - sls: ceph.logrotate
```

* Save the file

Verify that the orchestration file works.

```
# salt-run state.orch ceph.stage.prep.logrotate
```

The last file is the custom one which includes the additional step with the original steps.

* Create /srv/salt/ceph/stage/prep/custom.sls.  Enter the following:

```
include:
  - .logrotate
  - .master
  - .minion
```

* Save the file

Finally, override the default behavior.

* Edit /srv/pillar/ceph/stack/global.yml

* Add `stage_prep: custom`

* Save the file

Verify that Stage 0 works

```
# salt-run state.orch ceph.stage.0
```

Note that the global.yml file is chosen and not the /srv/pillar/ceph/stack/ceph/cluster.yml.  During the Prep stage, no minion belongs to the ceph cluster and will not have access to any settings in cluster.yml.
