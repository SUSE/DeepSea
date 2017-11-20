#
# spec file for package deepsea
#
# Copyright (c) 2016 SUSE LINUX GmbH, Nuernberg, Germany.
#
# All modifications and additions to the file contributed by third parties
# remain the property of their copyright owners, unless otherwise agreed
# upon. The license for this file, and modifications and additions to the
# file, is the same license as for the pristine package itself (unless the
# license for the pristine package is not an Open Source License, in which
# case the license is the MIT License). An "Open Source License" is a
# license that conforms to the Open Source Definition (Version 1.9)
# published by the Open Source Initiative.

# Please submit bugfixes or comments via http://bugs.opensuse.org/
#

# unify libexec for all targets
%global _libexecdir %{_exec_prefix}/lib


# See also http://en.opensuse.org/openSUSE:Shared_library_packaging_policy

Name:           deepsea
Version:        0.8
Release:        0
Summary:        Salt solution for deploying and managing Ceph

License:        GPL-3.0
Group:          System/Libraries
Url:            https://github.com/suse/deepsea
Source0:        %{name}-%{version}.tar.bz2

BuildRequires:  salt-master
BuildRequires:  python-setuptools
Requires:       salt-master
Requires:       salt-minion
Requires:       salt-api
Requires:       python-ipaddress
Requires:       python-netaddr
Requires:       python-rados
Requires:       python-setuptools
Requires:       python-click
BuildRoot:      %{_tmppath}/%{name}-%{version}-build
BuildArch:      noarch

%description
A collection of Salt files providing a deployment of Ceph as a series of stages.


%prep
%setup

%build
make DESTDIR=%{buildroot} pyc
# rewrite version number in deepsea.spec that lives inside the tarball
sed -i 's/^Version:.*/Version: %{version}/g' deepsea.spec

%install
make DESTDIR=%{buildroot} DOCDIR=%{_docdir} copy-files
%__rm -f %{buildroot}/%{_mandir}/man?/*.gz
%__gzip %{buildroot}/%{_mandir}/man?/deepsea*
python setup.py install --prefix=%{_prefix} --root=%{buildroot}

%post
if [ $1 -eq 1 ] ; then
  # Initialize to most likely value
  sed -i '/^master_minion:/s!_REPLACE_ME_!'`hostname -f`'!' /srv/pillar/ceph/master_minion.sls
fi
# Initialize the shared secret key
sed -i '/^sharedsecret: /s!{{ shared_secret }}!'`cat /proc/sys/kernel/random/uuid`'!' /etc/salt/master.d/sharedsecret.conf
chown salt:salt /etc/salt/master.d/sharedsecret.conf
# Restart salt-master if it's running, so it picks up
# the config changes in /etc/salt/master.d/modules.conf
systemctl try-restart salt-master > /dev/null 2>&1 || :
systemctl try-restart salt-api > /dev/null 2>&1 || :

%postun

%files
%defattr(-,root,root,-)
%{_bindir}/deepsea
%{python_sitelib}/deepsea/
%{python_sitelib}/deepsea-%{version}-py%{python_version}.egg-info
/srv/modules/pillar/stack.py*
%dir /srv/modules/runners
%dir %attr(0755, salt, salt) /srv/pillar/ceph
%dir %attr(0755, salt, salt) /srv/pillar/ceph/stack
%dir %attr(0755, salt, salt) /srv/pillar/ceph/benchmarks
%dir %attr(0755, salt, salt) /srv/pillar/ceph/benchmarks/collections
%dir %attr(0755, salt, salt) /srv/pillar/ceph/benchmarks/fio
%dir %attr(0755, salt, salt) /srv/pillar/ceph/benchmarks/templates
%dir /srv/modules
%dir /srv/modules/pillar
%dir /srv/salt/_modules
%dir %attr(0755, salt, salt) /srv/salt/ceph
%dir /srv/salt/ceph/admin
%dir %attr(0700, salt, salt) /srv/salt/ceph/admin/cache
%dir /srv/salt/ceph/admin/files
%dir /srv/salt/ceph/admin/key
%dir /srv/salt/ceph/benchmarks
%dir /srv/salt/ceph/cephfs
%dir /srv/salt/ceph/cephfs/benchmarks
%dir /srv/salt/ceph/cephfs/benchmarks/files
%dir /srv/salt/ceph/salt-api
%dir /srv/salt/ceph/salt-api/files
%dir /srv/salt/ceph/configuration
%dir /srv/salt/ceph/configuration/files
%dir /srv/salt/ceph/configuration/files/ceph.conf.d
%dir /srv/salt/ceph/configuration/files/ceph.conf.checksum
%dir %attr(0700, salt, salt) /srv/salt/ceph/configuration/files/ceph.conf.checksum
%dir /srv/salt/ceph/configuration/check
%dir /srv/salt/ceph/configuration/create
%dir /srv/salt/ceph/diagnose
%dir /srv/salt/ceph/ganesha
%dir /srv/salt/ceph/ganesha/auth
%dir %attr(0700, salt, salt) /srv/salt/ceph/ganesha/cache
%dir /srv/salt/ceph/ganesha/config
%dir /srv/salt/ceph/ganesha/configure
%dir /srv/salt/ceph/ganesha/files
%dir /srv/salt/ceph/ganesha/key
%dir /srv/salt/ceph/ganesha/keyring
%dir /srv/salt/ceph/ganesha/install
%dir /srv/salt/ceph/ganesha/restart
%dir /srv/salt/ceph/ganesha/restart/force
%dir /srv/salt/ceph/ganesha/restart/controlled
%dir /srv/salt/ceph/ganesha/service
%dir /srv/salt/ceph/igw
%dir %attr(0700, salt, salt) /srv/salt/ceph/igw/cache
%dir /srv/salt/ceph/igw/config
%dir /srv/salt/ceph/igw/files
%dir /srv/salt/ceph/igw/import
%dir /srv/salt/ceph/igw/key
%dir /srv/salt/ceph/igw/auth
%dir /srv/salt/ceph/igw/keyring
%dir /srv/salt/ceph/igw/restart
%dir /srv/salt/ceph/igw/sysconfig
%dir /srv/salt/ceph/mds
%dir %attr(0700, salt, salt) /srv/salt/ceph/mds/cache
%dir /srv/salt/ceph/mds/files
%dir /srv/salt/ceph/mds/key
%dir /srv/salt/ceph/mds/auth
%dir /srv/salt/ceph/mds/keyring
%dir /srv/salt/ceph/mds/pools
%dir /srv/salt/ceph/mds/restart
%dir /srv/salt/ceph/mds/restart/force
%dir /srv/salt/ceph/mds/restart/controlled
%dir /srv/salt/ceph/mgr
%dir %attr(0700, salt, salt) /srv/salt/ceph/mgr/cache
%dir /srv/salt/ceph/mgr/files
%dir /srv/salt/ceph/mgr/key
%dir /srv/salt/ceph/mgr/auth
%dir /srv/salt/ceph/mgr/keyring
%dir /srv/salt/ceph/mgr/restart
%dir /srv/salt/ceph/mgr/restart/force
%dir /srv/salt/ceph/mgr/restart/controlled
%dir /srv/salt/ceph/migrate
%dir /srv/salt/ceph/migrate/nodes
%dir /srv/salt/ceph/migrate/osds
%dir /srv/salt/ceph/migrate/policy
%dir /srv/salt/ceph/migrate/subvolume
%dir /srv/salt/ceph/mines
%dir /srv/salt/ceph/mines/files
%dir /srv/salt/ceph/mon
%dir %attr(0700, salt, salt) /srv/salt/ceph/mon/cache
%dir /srv/salt/ceph/mon/files
%dir /srv/salt/ceph/mon/key
%dir /srv/salt/ceph/mon/restart
%dir /srv/salt/ceph/mon/restart/force
%dir /srv/salt/ceph/mon/restart/controlled
%dir /srv/salt/ceph/monitoring
%dir /srv/salt/ceph/monitoring/grafana
%dir /srv/salt/ceph/monitoring/grafana/files
%dir /srv/salt/ceph/monitoring/prometheus
%dir /srv/salt/ceph/monitoring/prometheus/exporters
%dir /srv/salt/ceph/monitoring/prometheus/exporters/files
%dir /srv/salt/ceph/monitoring/prometheus/files
%dir /srv/salt/ceph/noout
%dir /srv/salt/ceph/noout/set
%dir /srv/salt/ceph/noout/unset
%dir /srv/salt/ceph/openattic
%dir /srv/salt/ceph/openattic/auth
%dir %attr(0700, salt, salt) /srv/salt/ceph/openattic/cache
%dir /srv/salt/ceph/openattic/files
%dir /srv/salt/ceph/openattic/key
%dir /srv/salt/ceph/openattic/keyring
%dir /srv/salt/ceph/openattic/oaconfig
%dir /srv/salt/ceph/openattic/restart
%dir /srv/salt/ceph/openattic/restart/force
%dir /srv/salt/ceph/openattic/restart/controlled
%dir /srv/salt/ceph/osd
%dir %attr(0700, salt, salt) /srv/salt/ceph/osd/cache
%dir /srv/salt/ceph/osd/files
%dir /srv/salt/ceph/osd/key
%dir /srv/salt/ceph/osd/auth
%dir /srv/salt/ceph/osd/grains
%dir /srv/salt/ceph/osd/keyring
%dir /srv/salt/ceph/osd/restart
%dir /srv/salt/ceph/osd/restart/force
%dir /srv/salt/ceph/osd/restart/controlled
%dir /srv/salt/ceph/osd/restart/parallel
%dir /srv/salt/ceph/osd/scheduler
%dir /srv/salt/ceph/packages
%dir /srv/salt/ceph/packages/common
%dir /srv/salt/ceph/packages/remove
%dir /srv/salt/ceph/pool
%dir /srv/salt/ceph/purge
%dir /srv/salt/ceph/rbd
%dir /srv/salt/ceph/rbd/benchmarks
%dir /srv/salt/ceph/rbd/benchmarks/files
%dir /srv/salt/ceph/reactor
%dir /srv/salt/ceph/refresh
%dir /srv/salt/ceph/repo
%dir /srv/salt/ceph/redeploy
%dir /srv/salt/ceph/redeploy/osds
%dir /srv/salt/ceph/redeploy/nodes
%dir /srv/salt/ceph/remove
%dir /srv/salt/ceph/remove/ganesha
%dir /srv/salt/ceph/remove/igw
%dir /srv/salt/ceph/remove/igw/auth
%dir /srv/salt/ceph/remove/mon
%dir /srv/salt/ceph/remove/mds
%dir /srv/salt/ceph/remove/mgr
%dir /srv/salt/ceph/remove/migrated
%dir /srv/salt/ceph/remove/rgw
%dir /srv/salt/ceph/remove/storage
%dir /srv/salt/ceph/remove/storage/drain
%dir /srv/salt/ceph/remove/openattic
%dir /srv/salt/ceph/reset
%dir /srv/salt/ceph/rescind
%dir /srv/salt/ceph/rescind/admin
%dir /srv/salt/ceph/rescind/client-cephfs
%dir /srv/salt/ceph/rescind/client-iscsi
%dir /srv/salt/ceph/rescind/client-nfs
%dir /srv/salt/ceph/rescind/client-radosgw
%dir /srv/salt/ceph/rescind/benchmark-rbd
%dir /srv/salt/ceph/rescind/ganesha
%dir /srv/salt/ceph/rescind/igw
%dir /srv/salt/ceph/rescind/igw/keyring
%dir /srv/salt/ceph/rescind/igw/lrbd
%dir /srv/salt/ceph/rescind/igw/sysconfig
%dir /srv/salt/ceph/rescind/master
%dir /srv/salt/ceph/rescind/mds
%dir /srv/salt/ceph/rescind/mds/keyring
%dir /srv/salt/ceph/rescind/mgr
%dir /srv/salt/ceph/rescind/mgr/keyring
%dir /srv/salt/ceph/rescind/mon
%dir /srv/salt/ceph/rescind/rgw
%dir /srv/salt/ceph/rescind/rgw/keyring
%dir /srv/salt/ceph/rescind/rgw/monitoring
%dir /srv/salt/ceph/rescind/storage
%dir /srv/salt/ceph/rescind/storage/terminate
%dir /srv/salt/ceph/rescind/storage/keyring
%dir /srv/salt/ceph/rescind/openattic
%dir /srv/salt/ceph/rescind/openattic/keyring
%dir /srv/salt/ceph/restart
%dir /srv/salt/ceph/restart/osd
%dir /srv/salt/ceph/restart/mon
%dir /srv/salt/ceph/restart/mgr
%dir /srv/salt/ceph/restart/rgw
%dir /srv/salt/ceph/restart/igw
%dir /srv/salt/ceph/restart/mds
%dir /srv/salt/ceph/restart/ganesha
%dir /srv/salt/ceph/restart/openattic
%dir /srv/salt/ceph/rgw
%dir %attr(0700, salt, salt) /srv/salt/ceph/rgw/cache
%dir /srv/salt/ceph/rgw/files
%dir /srv/salt/ceph/rgw/key
%dir /srv/salt/ceph/rgw/auth
%dir /srv/salt/ceph/rgw/buckets
%dir /srv/salt/ceph/rgw/cert
%dir /srv/salt/ceph/rgw/keyring
%dir /srv/salt/ceph/rgw/restart
%dir /srv/salt/ceph/rgw/restart/force
%dir /srv/salt/ceph/rgw/restart/controlled
%dir /srv/salt/ceph/rgw/users
%dir /srv/salt/ceph/rgw/users/users.d
%dir /srv/salt/ceph/stage
%dir /srv/salt/ceph/stage/all
%dir /srv/salt/ceph/stage/cephfs
%dir /srv/salt/ceph/stage/configure
%dir /srv/salt/ceph/stage/deploy
%dir /srv/salt/ceph/stage/discovery
%dir /srv/salt/ceph/stage/iscsi
%dir /srv/salt/ceph/stage/ganesha
%dir /srv/salt/ceph/stage/openattic
%dir /srv/salt/ceph/stage/prep
%dir /srv/salt/ceph/stage/prep/master
%dir /srv/salt/ceph/stage/prep/minion
%dir /srv/salt/ceph/stage/radosgw
%dir /srv/salt/ceph/stage/removal
%dir /srv/salt/ceph/stage/services
%dir /srv/salt/ceph/tools
%dir /srv/salt/ceph/tools/benchmarks
%dir /srv/salt/ceph/tools/fio
%dir /srv/salt/ceph/tools/fio/files
%dir /srv/salt/ceph/sync
%dir /srv/salt/ceph/sysctl
%dir /srv/salt/ceph/sysctl/files
%dir /srv/salt/ceph/setosdflags
%dir /srv/salt/ceph/time
%dir /srv/salt/ceph/time/ntp
%dir /srv/salt/ceph/time/ntp/files
%dir /srv/salt/ceph/maintenance
%dir /srv/salt/ceph/maintenance/upgrade
%dir /srv/salt/ceph/maintenance/noout
%dir /srv/salt/ceph/maintenance/upgrade/master
%dir /srv/salt/ceph/maintenance/upgrade/minion
%dir /srv/salt/ceph/maintenance/upgrade/report
%dir /srv/salt/ceph/maintenance/upgrade/cleanup
%dir /srv/salt/ceph/upgrade
%dir /srv/salt/ceph/updates
%dir /srv/salt/ceph/updates/master
%dir /srv/salt/ceph/updates/salt
%dir /srv/salt/ceph/updates/restart
%dir /srv/salt/ceph/updates/regular
%dir /srv/salt/ceph/updates/kernel
%dir /srv/salt/ceph/wait
%dir /srv/salt/ceph/wait/1hour
%dir /srv/salt/ceph/wait/1hour/until
%dir /srv/salt/ceph/wait/1hour/until/OK
%dir /srv/salt/ceph/wait/2hours
%dir /srv/salt/ceph/wait/2hours/until
%dir /srv/salt/ceph/wait/2hours/until/OK
%dir /srv/salt/ceph/wait/4hours
%dir /srv/salt/ceph/wait/4hours/until
%dir /srv/salt/ceph/wait/4hours/until/OK
%dir /srv/salt/ceph/wait/until
%dir /srv/salt/ceph/wait/until/OK
%dir /srv/salt/ceph/wait/until/expired
%dir /srv/salt/ceph/wait/until/expired/30sec
%dir /srv/salt/ceph/warning
%dir /srv/salt/ceph/warning/noout
%dir /srv/salt/ceph/processes
%{_mandir}/man7/deepsea*.7.gz
%{_mandir}/man5/deepsea*.5.gz
%{_mandir}/man1/deepsea*.1.gz
%config(noreplace) %attr(-, salt, salt) /etc/salt/master.d/*.conf
/srv/modules/runners/*.py*
%config %attr(-, salt, salt) /srv/pillar/top.sls
%config %attr(-, salt, salt) /srv/pillar/ceph/init.sls
%config %attr(-, salt, salt) /srv/pillar/ceph/benchmarks/config.yml
%config %attr(-, salt, salt) /srv/pillar/ceph/benchmarks/benchmark.cfg
%config %attr(-, salt, salt) /srv/pillar/ceph/benchmarks/collections/*.yml
%config %attr(-, salt, salt) /srv/pillar/ceph/benchmarks/fio/*.yml
%config %attr(-, salt, salt) /srv/pillar/ceph/benchmarks/templates/*.j2
%config(noreplace) %attr(-, salt, salt) /srv/pillar/ceph/master_minion.sls
%config(noreplace) %attr(-, salt, salt) /srv/pillar/ceph/deepsea_minions.sls
%config %attr(-, salt, salt) /srv/pillar/ceph/stack/stack.cfg
/srv/salt/_modules/*.py*
%config /srv/salt/ceph/admin/*.sls
%config /srv/salt/ceph/admin/files/*.j2
%config /srv/salt/ceph/admin/key/*.sls
%config /srv/salt/ceph/benchmarks/*.sls
%config /srv/salt/ceph/cephfs/benchmarks/*.sls
%config /srv/salt/ceph/cephfs/benchmarks/files/keyring.j2
%config /srv/salt/ceph/salt-api/*.sls
%config /srv/salt/ceph/salt-api/files/*.conf*
%config /srv/salt/ceph/tools/benchmarks/*.sls
%config /srv/salt/ceph/tools/fio/*.sls
%config /srv/salt/ceph/tools/fio/files/fio.service
%config /srv/salt/ceph/configuration/*.sls
%config /srv/salt/ceph/configuration/check/*.sls
%config /srv/salt/ceph/configuration/create/*.sls
%config /srv/salt/ceph/configuration/files/*.conf
%config /srv/salt/ceph/configuration/files/*.j2
%config(noreplace) %attr(-, salt, salt) /srv/salt/ceph/configuration/files/ceph.conf.import
/srv/salt/ceph/configuration/files/ceph.conf.d/README
/srv/salt/ceph/diagnose/README.md
%config /srv/salt/ceph/diagnose/*.sls
%config /srv/salt/ceph/ganesha/*.sls
%config /srv/salt/ceph/ganesha/auth/*.sls
%config /srv/salt/ceph/ganesha/config/*.sls
%config /srv/salt/ceph/ganesha/configure/*.sls
%config /srv/salt/ceph/ganesha/files/*.j2
%config /srv/salt/ceph/ganesha/install/*.sls
%config /srv/salt/ceph/ganesha/key/*.sls
%config /srv/salt/ceph/ganesha/keyring/*.sls
%config /srv/salt/ceph/ganesha/restart/*.sls
%config /srv/salt/ceph/ganesha/restart/force/*.sls
%config /srv/salt/ceph/ganesha/restart/controlled/*.sls
%config /srv/salt/ceph/ganesha/service/*.sls
%config /srv/salt/ceph/igw/*.sls
%config /srv/salt/ceph/igw/files/*.j2
%config /srv/salt/ceph/igw/config/*.sls
%config /srv/salt/ceph/igw/import/*.sls
%config /srv/salt/ceph/igw/key/*.sls
%config /srv/salt/ceph/igw/auth/*.sls
%config /srv/salt/ceph/igw/keyring/*.sls
%config /srv/salt/ceph/igw/restart/*.sls
%config /srv/salt/ceph/igw/sysconfig/*.sls
%config /srv/salt/ceph/mds/*.sls
%config /srv/salt/ceph/mds/files/*.j2
%config /srv/salt/ceph/mds/key/*.sls
%config /srv/salt/ceph/mds/auth/*.sls
%config /srv/salt/ceph/mds/keyring/*.sls
%config /srv/salt/ceph/mds/pools/*.sls
%config /srv/salt/ceph/mds/restart/*.sls
%config /srv/salt/ceph/mds/restart/force/*.sls
%config /srv/salt/ceph/mds/restart/controlled/*.sls
%config /srv/salt/ceph/mgr/*.sls
%config /srv/salt/ceph/mgr/files/*.j2
%config /srv/salt/ceph/mgr/key/*.sls
%config /srv/salt/ceph/mgr/auth/*.sls
%config /srv/salt/ceph/mgr/keyring/*.sls
%config /srv/salt/ceph/mgr/restart/*.sls
%config /srv/salt/ceph/mgr/restart/force/*.sls
%config /srv/salt/ceph/mgr/restart/controlled/*.sls
%config /srv/salt/ceph/migrate/nodes/*.sls
%config /srv/salt/ceph/migrate/osds/*.sls
%config /srv/salt/ceph/migrate/policy/*.sls
%config /srv/salt/ceph/migrate/subvolume/*.sls
%config /srv/salt/ceph/mines/*.sls
%config /srv/salt/ceph/mines/files/*.conf
%config /srv/salt/ceph/mon/*.sls
%config /srv/salt/ceph/mon/files/*.j2
%config /srv/salt/ceph/mon/key/*.sls
%config /srv/salt/ceph/mon/restart/*.sls
%config /srv/salt/ceph/mon/restart/force/*.sls
%config /srv/salt/ceph/mon/restart/controlled/*.sls
%config /srv/salt/ceph/monitoring/*.sls
%config /srv/salt/ceph/monitoring/grafana/*.sls
%config /srv/salt/ceph/monitoring/grafana/files/*.json
%config /srv/salt/ceph/monitoring/prometheus/*.sls
%config /srv/salt/ceph/monitoring/prometheus/exporters/*.sls
%config /srv/salt/ceph/monitoring/prometheus/exporters/files/*
%config /srv/salt/ceph/monitoring/prometheus/files/*.j2
%config /srv/salt/ceph/noout/set/*.sls
%config /srv/salt/ceph/noout/unset/*.sls
%config /srv/salt/ceph/openattic/*.sls
%config /srv/salt/ceph/openattic/auth/*.sls
%config /srv/salt/ceph/openattic/key/*.sls
%config /srv/salt/ceph/openattic/keyring/*.sls
%config /srv/salt/ceph/openattic/oaconfig/*.sls
%config /srv/salt/ceph/openattic/files/*.j2
%config /srv/salt/ceph/openattic/restart/*.sls
%config /srv/salt/ceph/openattic/restart/force/*.sls
%config /srv/salt/ceph/openattic/restart/controlled/*.sls
%config /srv/salt/ceph/osd/*.sls
%config /srv/salt/ceph/osd/files/*.j2
%config /srv/salt/ceph/osd/key/*.sls
%config /srv/salt/ceph/osd/auth/*.sls
%config /srv/salt/ceph/osd/grains/*.sls
%config /srv/salt/ceph/osd/keyring/*.sls
%config /srv/salt/ceph/osd/restart/*.sls
%config /srv/salt/ceph/osd/restart/force/*.sls
%config /srv/salt/ceph/osd/restart/controlled/*.sls
%config /srv/salt/ceph/osd/restart/parallel/*.sls
%config /srv/salt/ceph/osd/scheduler/*.sls
%config /srv/salt/ceph/packages/*.sls
%config /srv/salt/ceph/packages/common/*.sls
%config /srv/salt/ceph/packages/remove/*.sls
%config /srv/salt/ceph/pool/*.sls
%config /srv/salt/ceph/purge/*.sls
%config /srv/salt/ceph/rbd/benchmarks/*.sls
%config /srv/salt/ceph/rbd/benchmarks/files/keyring.j2
%config /srv/salt/ceph/reactor/*.sls
%config /srv/salt/ceph/refresh/*.sls
%config /srv/salt/ceph/repo/*.sls
%config /srv/salt/ceph/redeploy/nodes/*.sls
%config /srv/salt/ceph/redeploy/osds/*.sls
%config /srv/salt/ceph/remove/ganesha/*.sls
%config /srv/salt/ceph/remove/igw/auth/*.sls
%config /srv/salt/ceph/remove/mon/*.sls
%config /srv/salt/ceph/remove/mds/*.sls
%config /srv/salt/ceph/remove/migrated/*.sls
%config /srv/salt/ceph/remove/mgr/*.sls
%config /srv/salt/ceph/remove/openattic/*.sls
%config /srv/salt/ceph/remove/rgw/*.sls
%config /srv/salt/ceph/remove/storage/*.sls
%config /srv/salt/ceph/remove/storage/drain/*.sls
%config /srv/salt/ceph/rescind/*.sls
%config /srv/salt/ceph/rescind/admin/*.sls
%config /srv/salt/ceph/rescind/client-iscsi/*.sls
%config /srv/salt/ceph/rescind/client-cephfs/*.sls
%config /srv/salt/ceph/rescind/client-nfs/*.sls
%config /srv/salt/ceph/rescind/client-radosgw/*.sls
%config /srv/salt/ceph/rescind/benchmark-rbd/*.sls
%config /srv/salt/ceph/rescind/ganesha/*.sls
%config /srv/salt/ceph/rescind/igw/*.sls
%config /srv/salt/ceph/rescind/igw/keyring/*.sls
%config /srv/salt/ceph/rescind/igw/lrbd/*.sls
%config /srv/salt/ceph/rescind/igw/sysconfig/*.sls
%config /srv/salt/ceph/rescind/master/*.sls
%config /srv/salt/ceph/rescind/mds/*.sls
%config /srv/salt/ceph/rescind/mds/keyring/*.sls
%config /srv/salt/ceph/rescind/mgr/*.sls
%config /srv/salt/ceph/rescind/mgr/keyring/*.sls
%config /srv/salt/ceph/rescind/mon/*.sls
%config /srv/salt/ceph/rescind/rgw/*.sls
%config /srv/salt/ceph/rescind/rgw/keyring/*.sls
%config /srv/salt/ceph/rescind/rgw/monitoring/*.sls
%config /srv/salt/ceph/rescind/storage/*.sls
%config /srv/salt/ceph/rescind/storage/keyring/*.sls
%config /srv/salt/ceph/rescind/openattic/*.sls
%config /srv/salt/ceph/rescind/openattic/keyring/*.sls
%config /srv/salt/ceph/reset/*.sls
%config /srv/salt/ceph/rescind/storage/terminate/*.sls
%config /srv/salt/ceph/restart/*.sls
%config /srv/salt/ceph/restart/osd/*.sls
%config /srv/salt/ceph/restart/mon/*.sls
%config /srv/salt/ceph/restart/mgr/*.sls
%config /srv/salt/ceph/restart/mds/*.sls
%config /srv/salt/ceph/restart/rgw/*.sls
%config /srv/salt/ceph/restart/igw/*.sls
%config /srv/salt/ceph/restart/ganesha/*.sls
%config /srv/salt/ceph/restart/openattic/*.sls
%config /srv/salt/ceph/rgw/*.sls
%config /srv/salt/ceph/rgw/files/*.j2
%config /srv/salt/ceph/rgw/files/*.yml
%config /srv/salt/ceph/rgw/key/*.sls
%config /srv/salt/ceph/rgw/auth/*.sls
%config /srv/salt/ceph/rgw/buckets/*.sls
%config /srv/salt/ceph/rgw/cert/*.sls
%config /srv/salt/ceph/rgw/keyring/*.sls
%config /srv/salt/ceph/rgw/restart/*.sls
%config /srv/salt/ceph/rgw/restart/force/*.sls
%config /srv/salt/ceph/rgw/restart/controlled/*.sls
%config /srv/salt/ceph/rgw/users/*.sls
%config /srv/salt/ceph/rgw/users/users.d/README
%config /srv/salt/ceph/stage/0
%config /srv/salt/ceph/stage/1
%config /srv/salt/ceph/stage/2
%config /srv/salt/ceph/stage/3
%config /srv/salt/ceph/stage/4
%config /srv/salt/ceph/stage/5
%config /srv/salt/ceph/stage/all/*.sls
%config /srv/salt/ceph/stage/cephfs/*.sls
%config /srv/salt/ceph/stage/configure/*.sls
%config /srv/salt/ceph/stage/deploy/*.sls
%config /srv/salt/ceph/stage/discovery/*.sls
%config /srv/salt/ceph/stage/iscsi/*.sls
%config /srv/salt/ceph/stage/ganesha/*.sls
%config /srv/salt/ceph/stage/openattic/*.sls
%config /srv/salt/ceph/stage/prep/*.sls
%config /srv/salt/ceph/stage/prep/master/*.sls
%config /srv/salt/ceph/stage/prep/minion/*.sls
%config /srv/salt/ceph/stage/radosgw/*.sls
%config /srv/salt/ceph/stage/removal/*.sls
%config /srv/salt/ceph/stage/services/*.sls
%config /srv/salt/ceph/sync/*.sls
%config /srv/salt/ceph/sysctl/*.sls
%config /srv/salt/ceph/sysctl/files/*.conf
%config /srv/salt/ceph/setosdflags/*.sls
%config /srv/salt/ceph/time/*.sls
%config /srv/salt/ceph/time/ntp/*.sls
%config /srv/salt/ceph/time/ntp/files/*.j2
%config /srv/salt/ceph/upgrade/*.sls
%config /srv/salt/ceph/maintenance/noout/*.sls
%config /srv/salt/ceph/maintenance/upgrade/*.sls
%config /srv/salt/ceph/maintenance/upgrade/master/*.sls
%config /srv/salt/ceph/maintenance/upgrade/minion/*.sls
%config /srv/salt/ceph/maintenance/upgrade/report/*.sls
%config /srv/salt/ceph/maintenance/upgrade/cleanup/*.sls
%config /srv/salt/ceph/tools/fio/*.sls
%config /srv/salt/ceph/tools/fio/files/fio.service
%config /srv/salt/ceph/updates/*.sls
%config /srv/salt/ceph/updates/restart/*.sls
%config /srv/salt/ceph/updates/master/*.sls
%config /srv/salt/ceph/updates/salt/*.sls
%config /srv/salt/ceph/updates/kernel/*.sls
%config /srv/salt/ceph/updates/regular/*.sls
%config /srv/salt/ceph/wait/*.sls
%config /srv/salt/ceph/wait/1hour/until/OK/*.sls
%config /srv/salt/ceph/wait/2hours/until/OK/*.sls
%config /srv/salt/ceph/wait/4hours/until/OK/*.sls
%config /srv/salt/ceph/wait/until/OK/*.sls
%config /srv/salt/ceph/wait/until/expired/30sec/*.sls
%config /srv/salt/ceph/warning/*.sls
%config /srv/salt/ceph/warning/noout/*.sls
%config /srv/salt/ceph/processes/*.sls
%dir %{_libexecdir}/deepsea
%dir %attr(-, root, root) %{_docdir}/%{name}
%{_docdir}/%{name}/*

%package qa
Summary:        DeepSea integration test scripts
Group:          System/Libraries
Recommends:     deepsea

%description qa
The deepsea-qa subpackage contains all the scripts used in DeepSeq
integration/regression testing. These scripts are "environment-agnostic" - see
the README for more information.

%files qa
%{_libexecdir}/deepsea/qa

%changelog
