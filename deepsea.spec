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


# See also http://en.opensuse.org/openSUSE:Shared_library_packaging_policy

Name:           deepsea
Version:        0.7.8
Release:        0
Summary:        Salt solution for deploying and managing Ceph

License:        GPL-3.0
Group:          System/Libraries
Url:            http://bugs.opensuse.org
Source0:        %{name}-%{version}.tar.gz

BuildRequires:  salt-master
Requires:       salt-master
Requires:       salt-minion
Requires:       python-ipaddress
%if 0%{?sle_version} == 120200 && 0%{?is_opensuse} == 1
Requires:       python-netaddr
%endif
BuildRoot:      %{_tmppath}/%{name}-%{version}-build
BuildArch:      noarch

%description
A collection of Salt files providing a deployment of Ceph as a series of stages.


%prep
%setup

%build

%install
make DESTDIR=%{buildroot} DOCDIR=%{_docdir} copy-files

%post
# Initialize to most likely value
sed -i '/^master_minion:/s!_REPLACE_ME_!'`hostname -f`'!' /srv/pillar/ceph/master_minion.sls
# change owner to salt, so deepsea can create proposals
chown -R salt /srv/pillar/ceph
# Restart salt-master if it's running, so it picks up
# the config changes in /etc/salt/master.d/modules.conf
systemctl try-restart salt-master > /dev/null 2>&1 || :

%postun

%files
%defattr(-,root,root,-)
/srv/modules/pillar/stack.py*
%dir /srv/modules/runners
%dir %attr(0755, salt, salt) /srv/pillar/ceph
%dir %attr(0755, salt, salt) /srv/pillar/ceph/stack
%dir %attr(0755, salt, salt) /srv/pillar/ceph/benchmark
%dir %attr(0755, salt, salt) /srv/pillar/ceph/benchmark/collections
%dir %attr(0755, salt, salt) /srv/pillar/ceph/benchmark/fio
%dir %attr(0755, salt, salt) /srv/pillar/ceph/benchmark/templates
%dir /srv/modules
%dir /srv/modules/pillar
%dir /srv/salt/_modules
%dir %attr(0755, salt, salt) /srv/salt/ceph
%dir /srv/salt/ceph/admin
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
%dir /srv/salt/ceph/configuration/check
%dir /srv/salt/ceph/diagnose
%dir /srv/salt/ceph/events
%dir /srv/salt/ceph/ganesha
%dir /srv/salt/ceph/ganesha/auth
%dir /srv/salt/ceph/ganesha/config
%dir /srv/salt/ceph/ganesha/configure
%dir /srv/salt/ceph/ganesha/files
%dir /srv/salt/ceph/ganesha/key
%dir /srv/salt/ceph/ganesha/keyring
%dir /srv/salt/ceph/ganesha/install
%dir /srv/salt/ceph/ganesha/restart
%dir /srv/salt/ceph/ganesha/service
%dir /srv/salt/ceph/igw
%dir /srv/salt/ceph/igw/config
%dir /srv/salt/ceph/igw/files
%dir /srv/salt/ceph/igw/import
%dir /srv/salt/ceph/igw/key
%dir /srv/salt/ceph/igw/auth
%dir /srv/salt/ceph/igw/keyring
%dir /srv/salt/ceph/igw/restart
%dir /srv/salt/ceph/igw/sysconfig
%dir /srv/salt/ceph/iperf
%dir /srv/salt/ceph/mds
%dir /srv/salt/ceph/mds/files
%dir /srv/salt/ceph/mds/key
%dir /srv/salt/ceph/mds/auth
%dir /srv/salt/ceph/mds/keyring
%dir /srv/salt/ceph/mds/pools
%dir /srv/salt/ceph/mds/restart
%dir /srv/salt/ceph/mines
%dir /srv/salt/ceph/mines/files
%dir /srv/salt/ceph/mon
%dir /srv/salt/ceph/mon/files
%dir /srv/salt/ceph/mon/key
%dir /srv/salt/ceph/mon/restart
%dir /srv/salt/ceph/monitoring
%dir /srv/salt/ceph/monitoring/prometheus
%dir /srv/salt/ceph/noout
%dir /srv/salt/ceph/noout/set
%dir /srv/salt/ceph/noout/unset
%dir /srv/salt/ceph/openattic
%dir /srv/salt/ceph/openattic/auth
%dir /srv/salt/ceph/openattic/files
%dir /srv/salt/ceph/openattic/key
%dir /srv/salt/ceph/openattic/keyring
%dir /srv/salt/ceph/openattic/oaconfig
%dir /srv/salt/ceph/osd
%dir /srv/salt/ceph/osd/files
%dir /srv/salt/ceph/osd/key
%dir /srv/salt/ceph/osd/auth
%dir /srv/salt/ceph/osd/keyring
%dir /srv/salt/ceph/osd/partition
%dir /srv/salt/ceph/osd/restart
%dir /srv/salt/ceph/osd/scheduler
%dir /srv/salt/ceph/packages
%dir /srv/salt/ceph/packages/common
%dir /srv/salt/ceph/pool
%dir /srv/salt/ceph/purge
%dir /srv/salt/ceph/reactor
%dir /srv/salt/ceph/refresh
%dir /srv/salt/ceph/repo
%dir /srv/salt/ceph/remove
%dir /srv/salt/ceph/remove/ganesha
%dir /srv/salt/ceph/remove/igw
%dir /srv/salt/ceph/remove/igw/auth
%dir /srv/salt/ceph/remove/mon
%dir /srv/salt/ceph/remove/mds
%dir /srv/salt/ceph/remove/rgw
%dir /srv/salt/ceph/remove/storage
%dir /srv/salt/ceph/remove/openattic
%dir /srv/salt/ceph/reset
%dir /srv/salt/ceph/rescind
%dir /srv/salt/ceph/rescind/admin
%dir /srv/salt/ceph/rescind/client-cephfs
%dir /srv/salt/ceph/rescind/client-iscsi
%dir /srv/salt/ceph/rescind/client-nfs
%dir /srv/salt/ceph/rescind/client-radosgw
%dir /srv/salt/ceph/rescind/ganesha
%dir /srv/salt/ceph/rescind/igw
%dir /srv/salt/ceph/rescind/igw/keyring
%dir /srv/salt/ceph/rescind/igw/lrbd
%dir /srv/salt/ceph/rescind/igw/sysconfig
%dir /srv/salt/ceph/rescind/master
%dir /srv/salt/ceph/rescind/mds-nfs
%dir /srv/salt/ceph/rescind/mds
%dir /srv/salt/ceph/rescind/mds/keyring
%dir /srv/salt/ceph/rescind/mon
%dir /srv/salt/ceph/rescind/rgw-nfs
%dir /srv/salt/ceph/rescind/rgw
%dir /srv/salt/ceph/rescind/rgw/keyring
%dir /srv/salt/ceph/rescind/storage
%dir /srv/salt/ceph/rescind/storage/keyring
%dir /srv/salt/ceph/rescind/openattic
%dir /srv/salt/ceph/rescind/openattic/keyring
%dir /srv/salt/ceph/restart
%dir /srv/salt/ceph/restart/osd
%dir /srv/salt/ceph/restart/mon
%dir /srv/salt/ceph/restart/rgw
%dir /srv/salt/ceph/restart/igw
%dir /srv/salt/ceph/restart/mds
%dir /srv/salt/ceph/restart/ganesha
%dir /srv/salt/ceph/rgw
%dir /srv/salt/ceph/rgw/files
%dir /srv/salt/ceph/rgw/key
%dir /srv/salt/ceph/rgw/auth
%dir /srv/salt/ceph/rgw/keyring
%dir /srv/salt/ceph/rgw/restart
%dir /srv/salt/ceph/rgw/users
%dir /srv/salt/ceph/stage
%dir /srv/salt/ceph/stage/all
%dir /srv/salt/ceph/stage/benchmark
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
%dir /srv/salt/ceph/sync
%dir /srv/salt/ceph/time
%dir /srv/salt/ceph/time/ntp
%dir /srv/salt/ceph/time/ntp/files
%dir /srv/salt/ceph/maintenance
%dir /srv/salt/ceph/maintenance/upgrade
%dir /srv/salt/ceph/maintenance/noout
%dir /srv/salt/ceph/maintenance/upgrade/master
%dir /srv/salt/ceph/maintenance/upgrade/minion
%dir /srv/salt/ceph/upgrade
%dir /srv/salt/ceph/updates
%dir /srv/salt/ceph/updates/master
%dir /srv/salt/ceph/updates/salt
%dir /srv/salt/ceph/updates/restart
%dir /srv/salt/ceph/updates/regular
%dir /srv/salt/ceph/updates/kernel
%dir /srv/salt/ceph/wait
%dir /srv/salt/ceph/warning
%dir /srv/salt/ceph/warning/noout
%dir /srv/salt/ceph/processes
%config(noreplace) /etc/salt/master.d/*.conf
%config /srv/modules/runners/*.py*
%config /srv/pillar/top.sls
%config /srv/pillar/ceph/init.sls
%config /srv/pillar/ceph/benchmark/config.yml
%config /srv/pillar/ceph/benchmark/benchmark.cfg
%config /srv/pillar/ceph/benchmark/collections/*.yml
%config /srv/pillar/ceph/benchmark/fio/*.yml
%config /srv/pillar/ceph/benchmark/templates/*.j2
%config(noreplace) /srv/pillar/ceph/master_minion.sls
%config /srv/pillar/ceph/stack/stack.cfg
%config /srv/salt/_modules/*.py*
%config /srv/salt/ceph/admin/*.sls
%config /srv/salt/ceph/admin/files/*.j2
%config /srv/salt/ceph/admin/key/*.sls
%config /srv/salt/ceph/benchmarks/*.sls
%config /srv/salt/ceph/cephfs/benchmarks/*.sls
%config /srv/salt/ceph/cephfs/benchmarks/files/fio.service
%config /srv/salt/ceph/salt-api/*.sls
%config /srv/salt/ceph/salt-api/files/*.conf*
%config /srv/salt/ceph/configuration/*.sls
%config /srv/salt/ceph/configuration/check/*.sls
%config /srv/salt/ceph/configuration/files/ceph.conf*
/srv/salt/ceph/diagnose/README.md
%config /srv/salt/ceph/diagnose/*.sls
%config /srv/salt/ceph/events/*.sls
%config /srv/salt/ceph/ganesha/*.sls
%config /srv/salt/ceph/ganesha/auth/*.sls
%config /srv/salt/ceph/ganesha/config/*.sls
%config /srv/salt/ceph/ganesha/configure/*.sls
%config /srv/salt/ceph/ganesha/files/*.j2
%config /srv/salt/ceph/ganesha/files/ganesha.service
%config /srv/salt/ceph/ganesha/install/*.sls
%config /srv/salt/ceph/ganesha/key/*.sls
%config /srv/salt/ceph/ganesha/keyring/*.sls
%config /srv/salt/ceph/ganesha/restart/*.sls
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
%config /srv/salt/ceph/iperf/*.sls
%config /srv/salt/ceph/iperf/*.service
%config /srv/salt/ceph/iperf/*.py*
%config /srv/salt/ceph/mds/*.sls
%config /srv/salt/ceph/mds/files/*.j2
%config /srv/salt/ceph/mds/key/*.sls
%config /srv/salt/ceph/mds/auth/*.sls
%config /srv/salt/ceph/mds/keyring/*.sls
%config /srv/salt/ceph/mds/pools/*.sls
%config /srv/salt/ceph/mds/restart/*.sls
%config /srv/salt/ceph/mines/*.sls
%config /srv/salt/ceph/mines/files/*.conf
%config /srv/salt/ceph/mon/*.sls
%config /srv/salt/ceph/mon/files/*.j2
%config /srv/salt/ceph/mon/key/*.sls
%config /srv/salt/ceph/mon/restart/*.sls
%config /srv/salt/ceph/monitoring/*.sls
%config /srv/salt/ceph/monitoring/prometheus/*.sls
%config /srv/salt/ceph/noout/set/*.sls
%config /srv/salt/ceph/noout/unset/*.sls
%config /srv/salt/ceph/openattic/*.sls
%config /srv/salt/ceph/openattic/auth/*.sls
%config /srv/salt/ceph/openattic/key/*.sls
%config /srv/salt/ceph/openattic/keyring/*.sls
%config /srv/salt/ceph/openattic/oaconfig/*.sls
%config /srv/salt/ceph/openattic/files/*.j2
%config /srv/salt/ceph/osd/*.sls
%config /srv/salt/ceph/osd/files/*.j2
%config /srv/salt/ceph/osd/key/*.sls
%config /srv/salt/ceph/osd/auth/*.sls
%config /srv/salt/ceph/osd/keyring/*.sls
%config /srv/salt/ceph/osd/partition/*.sls
%config /srv/salt/ceph/osd/restart/*.sls
%config /srv/salt/ceph/osd/scheduler/*.sls
%config /srv/salt/ceph/packages/*.sls
%config /srv/salt/ceph/packages/common/*.sls
%config /srv/salt/ceph/pool/*.sls
%config /srv/salt/ceph/purge/*.sls
%config /srv/salt/ceph/reactor/*.sls
%config /srv/salt/ceph/refresh/*.sls
%config /srv/salt/ceph/repo/*.sls
%config /srv/salt/ceph/remove/ganesha/*.sls
%config /srv/salt/ceph/remove/igw/auth/*.sls
%config /srv/salt/ceph/remove/mon/*.sls
%config /srv/salt/ceph/remove/mds/*.sls
%config /srv/salt/ceph/remove/rgw/*.sls
%config /srv/salt/ceph/remove/storage/*.sls
%config /srv/salt/ceph/remove/openattic/*.sls
%config /srv/salt/ceph/rescind/*.sls
%config /srv/salt/ceph/rescind/admin/*.sls
%config /srv/salt/ceph/rescind/client-iscsi/*.sls
%config /srv/salt/ceph/rescind/client-cephfs/*.sls
%config /srv/salt/ceph/rescind/client-nfs/*.sls
%config /srv/salt/ceph/rescind/client-radosgw/*.sls
%config /srv/salt/ceph/rescind/ganesha/*.sls
%config /srv/salt/ceph/rescind/igw/*.sls
%config /srv/salt/ceph/rescind/igw/keyring/*.sls
%config /srv/salt/ceph/rescind/igw/lrbd/*.sls
%config /srv/salt/ceph/rescind/igw/sysconfig/*.sls
%config /srv/salt/ceph/rescind/master/*.sls
%config /srv/salt/ceph/rescind/mds-nfs/*.sls
%config /srv/salt/ceph/rescind/mds/*.sls
%config /srv/salt/ceph/rescind/mds/keyring/*.sls
%config /srv/salt/ceph/rescind/mon/*.sls
%config /srv/salt/ceph/rescind/rgw-nfs/*.sls
%config /srv/salt/ceph/rescind/rgw/*.sls
%config /srv/salt/ceph/rescind/rgw/keyring/*.sls
%config /srv/salt/ceph/rescind/storage/*.sls
%config /srv/salt/ceph/rescind/storage/keyring/*.sls
%config /srv/salt/ceph/rescind/openattic/*.sls
%config /srv/salt/ceph/rescind/openattic/keyring/*.sls
%config /srv/salt/ceph/reset/*.sls
%config /srv/salt/ceph/restart/*.sls
%config /srv/salt/ceph/restart/osd/*.sls
%config /srv/salt/ceph/restart/mon/*.sls
%config /srv/salt/ceph/restart/mds/*.sls
%config /srv/salt/ceph/restart/rgw/*.sls
%config /srv/salt/ceph/restart/igw/*.sls
%config /srv/salt/ceph/restart/ganesha/*.sls
%config /srv/salt/ceph/rgw/*.sls
%config /srv/salt/ceph/rgw/files/*.j2
%config /srv/salt/ceph/rgw/key/*.sls
%config /srv/salt/ceph/rgw/auth/*.sls
%config /srv/salt/ceph/rgw/keyring/*.sls
%config /srv/salt/ceph/rgw/restart/*.sls
%config /srv/salt/ceph/rgw/users/*.sls
%config /srv/salt/ceph/stage/0
%config /srv/salt/ceph/stage/1
%config /srv/salt/ceph/stage/2
%config /srv/salt/ceph/stage/3
%config /srv/salt/ceph/stage/4
%config /srv/salt/ceph/stage/5
%config /srv/salt/ceph/stage/all/*.sls
%config /srv/salt/ceph/stage/benchmark/*.sls
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
%config /srv/salt/ceph/time/*.sls
%config /srv/salt/ceph/time/ntp/*.sls
%config /srv/salt/ceph/time/ntp/files/*.j2
%config /srv/salt/ceph/upgrade/*.sls
%config /srv/salt/ceph/maintenance/noout/*.sls
%config /srv/salt/ceph/maintenance/upgrade/*.sls
%config /srv/salt/ceph/maintenance/upgrade/master/*.sls
%config /srv/salt/ceph/maintenance/upgrade/minion/*.sls
%config /srv/salt/ceph/updates/*.sls
%config /srv/salt/ceph/updates/restart/*.sls
%config /srv/salt/ceph/updates/master/*.sls
%config /srv/salt/ceph/updates/salt/*.sls
%config /srv/salt/ceph/updates/kernel/*.sls
%config /srv/salt/ceph/updates/regular/*.sls
%config /srv/salt/ceph/wait/*.sls
%config /srv/salt/ceph/warning/*.sls
%config /srv/salt/ceph/warning/noout/*.sls
%config /srv/salt/ceph/processes/*.sls
%doc
%dir %attr(-, root, root) %{_docdir}/%{name}
%{_docdir}/%{name}/*


%changelog
* Thu Sep  8 2016 Eric Jackson
-
