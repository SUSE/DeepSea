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
Version:        0.6.5
Release:        0
Summary:        Salt solution for deploying and managing Ceph

License:        GPL-3.0
Group:          System/Libraries
Url:            http://bugs.opensuse.org
Source0:        deepsea-%{version}.tar.gz

BuildRequires:  salt-master
Requires:       salt-master
BuildRoot:      %{_tmppath}/%{name}-%{version}-build
BuildArch:      noarch

%description
A collection of Salt files providing a deployment of Ceph as a series of stages.


%prep
%setup

%build

%install
make DESTDIR=%{buildroot} install

%post 
# Initialize to most likely value
sed -i '/^master_minion:/s!_REPLACE_ME_!'`hostname -f`'!' /srv/pillar/ceph/master_minion.sls
# Restart salt-master if it's running, so it picks up
# the config changes in /etc/salt/master.d/modules.conf
systemctl try-restart salt-master > /dev/null 2>&1 || :

%postun 

%files
%defattr(-,root,root,-)
/srv/modules/pillar/stack.py
%dir /srv/modules/runners
%dir %attr(0755, salt, salt) /srv/pillar/ceph
%dir %attr(0755, salt, salt) /srv/pillar/ceph/stack
%dir /srv/modules
%dir /srv/modules/pillar
%dir /srv/salt/_modules
%dir %attr(0755, salt, salt) /srv/salt/ceph
%dir /srv/salt/ceph/admin
%dir /srv/salt/ceph/admin/files
%dir /srv/salt/ceph/admin/key
%dir /srv/salt/ceph/configuration
%dir /srv/salt/ceph/configuration/files
%dir /srv/salt/ceph/configuration/check
%dir /srv/salt/ceph/diagnose
%dir /srv/salt/ceph/events
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
%dir /srv/salt/ceph/reactor
%dir /srv/salt/ceph/refresh
%dir /srv/salt/ceph/repo
%dir /srv/salt/ceph/remove
%dir /srv/salt/ceph/remove/igw
%dir /srv/salt/ceph/remove/igw/auth
%dir /srv/salt/ceph/remove/mon
%dir /srv/salt/ceph/remove/mds
%dir /srv/salt/ceph/remove/rgw
%dir /srv/salt/ceph/remove/storage
%dir /srv/salt/ceph/rescind
%dir /srv/salt/ceph/rescind/admin
%dir /srv/salt/ceph/rescind/client-cephfs
%dir /srv/salt/ceph/rescind/client-iscsi
%dir /srv/salt/ceph/rescind/client-radosgw
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
%dir /srv/salt/ceph/restart
%dir /srv/salt/ceph/rgw
%dir /srv/salt/ceph/rgw/files
%dir /srv/salt/ceph/rgw/key
%dir /srv/salt/ceph/rgw/auth
%dir /srv/salt/ceph/rgw/keyring
%dir /srv/salt/ceph/rgw/restart
%dir /srv/salt/ceph/stage
%dir /srv/salt/ceph/stage/all
%dir /srv/salt/ceph/stage/benchmark
%dir /srv/salt/ceph/stage/cephfs
%dir /srv/salt/ceph/stage/configure
%dir /srv/salt/ceph/stage/deploy
%dir /srv/salt/ceph/stage/discovery
%dir /srv/salt/ceph/stage/iscsi
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
%dir /srv/salt/ceph/updates
%dir /srv/salt/ceph/updates/restart
%dir /srv/salt/ceph/wait
%config(noreplace) /etc/salt/master.d/*.conf
%config /srv/modules/runners/*.py
%config /srv/pillar/top.sls
/srv/pillar/ceph/README
%config /srv/pillar/ceph/init.sls
%config(noreplace) /srv/pillar/ceph/master_minion.sls
%config /srv/pillar/ceph/stack/stack.cfg
%config /srv/salt/_modules/*.py
%config /srv/salt/ceph/admin/*.sls
%config /srv/salt/ceph/admin/files/*.j2
%config /srv/salt/ceph/admin/key/*.sls
%config /srv/salt/ceph/configuration/*.sls
%config /srv/salt/ceph/configuration/check/*.sls
%config /srv/salt/ceph/configuration/files/ceph.conf*
%config /srv/salt/ceph/diagnose/*.sls
%config /srv/salt/ceph/events/*.sls
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
%config /srv/salt/ceph/reactor/*.sls
%config /srv/salt/ceph/refresh/*.sls
%config /srv/salt/ceph/repo/*.sls
%config /srv/salt/ceph/remove/igw/auth/*.sls
%config /srv/salt/ceph/remove/mon/*.sls
%config /srv/salt/ceph/remove/mds/*.sls
%config /srv/salt/ceph/remove/rgw/*.sls
%config /srv/salt/ceph/remove/storage/*.sls
%config /srv/salt/ceph/rescind/*.sls
%config /srv/salt/ceph/rescind/admin/*.sls
%config /srv/salt/ceph/rescind/client-iscsi/*.sls
%config /srv/salt/ceph/rescind/client-cephfs/*.sls
%config /srv/salt/ceph/rescind/client-radosgw/*.sls
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
%config /srv/salt/ceph/restart/*.sls
%config /srv/salt/ceph/rgw/*.sls
%config /srv/salt/ceph/rgw/files/*.j2
%config /srv/salt/ceph/rgw/key/*.sls
%config /srv/salt/ceph/rgw/auth/*.sls
%config /srv/salt/ceph/rgw/keyring/*.sls
%config /srv/salt/ceph/rgw/restart/*.sls
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
%config /srv/salt/ceph/updates/*.sls
%config /srv/salt/ceph/updates/restart/*.sls
%config /srv/salt/ceph/wait/*.sls
%doc
%dir %attr(-, root, root) %{_docdir}/%{name}
%{_docdir}/%{name}/*


%changelog
* Thu Sep  8 2016 Eric Jackson
- 
