* syslog

syslog allows centralization of your log files on a single server. The default
implementation used in SUSE linux is called 'rsyslog'.

** rsyslog server setup

*** Setting up the pillar data

To install this service first give add the role 'rsyslog' to the servers roles.

    # cat /srv/pillar/ceph/cluster/rsyslog.sls
    cluster: ceph
    roles:
    - rsyslog

Where rsyslog in the path corresponds to the shortened minion id node you wish
the rsyslog server to be installed on.

*** Installing rsyslog server

Then by running the following command can add the server:

    salt-run --state-output=changes state.orch ceph.stage.rsyslog.server

** rsyslog client setup

All nodes must have the property rsyslog_ipv4.

As an example this can be done by adding the property as


    # cat /srv/pillar/rsyslog/init.sls
    rsyslog_ipv4: 192.168.43.77

And adding the include for this to all nodes for example:

    # cat /srv/pillar/top.sls
    base:
      '*':
        - ceph
        - rsyslog

Where the last line includes the property for all rsyslog servers.

*** Installing rsyslog client

To make all ceph nodes log to rsyslog run the following command.

    salt-run --state-output=changes state.orch ceph.stage.rsyslog.client

*** instructing ceph to use syslog.

Ceph need to be told to use syslog. This is done by adding the value line:

    log_to_syslog = true

TO the file /etc/ceph/(ceph_cluster_name}.conf where {ceph_cluster_name} is the
cluster name you gave to your ceph config file, this is by default "ceph".

This can be done automatically by regenerating it using deepsea or by running
the command:

    salt '*' state.sls  ceph.configuration.default

Where '*' is the quoted regex matching your minions.
