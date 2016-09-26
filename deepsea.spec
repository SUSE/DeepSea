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
Version:        0.4.5
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

%build
%__tar xvzf %{SOURCE0}

%install
install -d -m 755 %{buildroot}%{_mandir}/man8

cd %{name}

install -d -m 755 %{buildroot}/etc/salt/master.d
install -m 644 etc/salt/master.d/modules.conf %{buildroot}/etc/salt/master.d/
install -m 644 etc/salt/master.d/reactor.conf %{buildroot}/etc/salt/master.d/

install -d -m 755 %{buildroot}%{_docdir}/%{name}
install -m 644 LICENSE %{buildroot}%{_docdir}/%{name}
install -m 644 README.md %{buildroot}%{_docdir}/%{name}

install -d -m 755 %{buildroot}%{_docdir}/%{name}/examples
install -m 644 doc/examples/policy.cfg-rolebased %{buildroot}%{_docdir}/%{name}/examples
install -m 644 doc/examples/policy.cfg-generic %{buildroot}%{_docdir}/%{name}/examples
install -m 644 doc/examples/policy.cfg-regex %{buildroot}%{_docdir}/%{name}/examples

# Included in Salt 2016.3
install -d -m 755 %{buildroot}/srv/modules/pillar
install -m 644 srv/modules/pillar/stack.py %{buildroot}/srv/modules/pillar

%define _runners srv/modules/runners
install -d -m 755 %{buildroot}/%{_runners}
install -m 644 %{_runners}/__init__.py %{buildroot}/%{_runners}
install -m 644 %{_runners}/bootstrap.py %{buildroot}/%{_runners}
install -m 644 %{_runners}/check.py %{buildroot}/%{_runners}
install -m 644 %{_runners}/configure.py %{buildroot}/%{_runners}
install -m 644 %{_runners}/filequeue.py %{buildroot}/%{_runners}
install -m 644 %{_runners}/minions.py %{buildroot}/%{_runners}
install -m 644 %{_runners}/populate.py %{buildroot}/%{_runners}
install -m 644 %{_runners}/push.py %{buildroot}/%{_runners}
install -m 644 %{_runners}/ready.py %{buildroot}/%{_runners}
install -m 644 %{_runners}/select.py %{buildroot}/%{_runners}
install -m 644 %{_runners}/validate.py %{buildroot}/%{_runners}

%define _pillar srv/pillar
install -d -m 755 %{buildroot}/%{_pillar}/ceph
install -m 644 %{_pillar}/ceph/cluster/README %{buildroot}/%{_pillar}/ceph
install -m 644 %{_pillar}/ceph/init.sls %{buildroot}/%{_pillar}/ceph
install -m 644 %{_pillar}/ceph/master_minion.sls %{buildroot}/%{_pillar}/ceph

install -d -m 755 %{buildroot}/%{_pillar}/ceph/stack
install -m 644 %{_pillar}/ceph/stack/stack.cfg %{buildroot}/%{_pillar}/ceph/stack/stack.cfg

install -m 644 %{_pillar}/top.sls %{buildroot}/%{_pillar}

install -d -m 755 %{buildroot}/srv/salt/_modules
install -m 644 srv/salt/_modules/keyring.py %{buildroot}/srv/salt/_modules
install -m 644 srv/salt/_modules/cephdisks.py %{buildroot}/srv/salt/_modules
install -m 644 srv/salt/_modules/freedisks.py %{buildroot}/srv/salt/_modules
install -m 644 srv/salt/_modules/retry.py %{buildroot}/srv/salt/_modules
install -m 644 srv/salt/_modules/wait.py %{buildroot}/srv/salt/_modules
install -m 644 srv/salt/_modules/zypper_locks.py %{buildroot}/srv/salt/_modules

%define _saltceph srv/salt/ceph
install -d -m 755 %{buildroot}/%{_saltceph}/admin
install -m 644 %{_saltceph}/admin/default.sls %{buildroot}/%{_saltceph}/admin
install -m 644 %{_saltceph}/admin/init.sls %{buildroot}/%{_saltceph}/admin

install -d -m 755 %{buildroot}/%{_saltceph}/admin/key
install -m 644 %{_saltceph}/admin/key/default.sls %{buildroot}/%{_saltceph}/admin/key
install -m 644 %{_saltceph}/admin/key/init.sls %{buildroot}/%{_saltceph}/admin/key

install -d -m 755 %{buildroot}/%{_saltceph}/admin/files
install -m 644 %{_saltceph}/admin/files/keyring.j2 %{buildroot}/%{_saltceph}/admin/files

install -d -m 755 %{buildroot}/%{_saltceph}/configuration
install -m 644 %{_saltceph}/configuration/default.sls %{buildroot}/%{_saltceph}/configuration
install -m 644 %{_saltceph}/configuration/init.sls %{buildroot}/%{_saltceph}/configuration
install -d -m 755 %{buildroot}/%{_saltceph}/configuration/files
install -m 644 %{_saltceph}/configuration/files/ceph.conf.j2 %{buildroot}/%{_saltceph}/configuration/files


install -d -m 755 %{buildroot}/%{_saltceph}/events
install -m 644 %{_saltceph}/events/begin_prep.sls %{buildroot}/%{_saltceph}/events
install -m 644 %{_saltceph}/events/complete_prep.sls %{buildroot}/%{_saltceph}/events

install -d -m 755 %{buildroot}/%{_saltceph}/igw
install -m 644 %{_saltceph}/igw/default.sls %{buildroot}/%{_saltceph}/igw
install -m 644 %{_saltceph}/igw/init.sls %{buildroot}/%{_saltceph}/igw

install -d -m 755 %{buildroot}/%{_saltceph}/igw/files
install -m 644 %{_saltceph}/igw/files/sysconfig.lrbd.j2 %{buildroot}/%{_saltceph}/igw/files
install -m 644 %{_saltceph}/igw/files/keyring.j2 %{buildroot}/%{_saltceph}/igw/files

install -d -m 755 %{buildroot}/%{_saltceph}/igw/import
install -m 644 %{_saltceph}/igw/import/default.sls %{buildroot}/%{_saltceph}/igw/import
install -m 644 %{_saltceph}/igw/import/init.sls %{buildroot}/%{_saltceph}/igw/import

install -d -m 755 %{buildroot}/%{_saltceph}/igw/key
install -m 644 %{_saltceph}/igw/key/default.sls %{buildroot}/%{_saltceph}/igw/key
install -m 644 %{_saltceph}/igw/key/init.sls %{buildroot}/%{_saltceph}/igw/key
install -m 644 %{_saltceph}/igw/key/shared.sls %{buildroot}/%{_saltceph}/igw/key

install -d -m 755 %{buildroot}/%{_saltceph}/igw/auth
install -m 644 %{_saltceph}/igw/auth/default.sls %{buildroot}/%{_saltceph}/igw/auth
install -m 644 %{_saltceph}/igw/auth/init.sls %{buildroot}/%{_saltceph}/igw/auth
install -m 644 %{_saltceph}/igw/auth/shared.sls %{buildroot}/%{_saltceph}/igw/auth

install -d -m 755 %{buildroot}/%{_saltceph}/igw/keyring
install -m 644 %{_saltceph}/igw/keyring/default.sls %{buildroot}/%{_saltceph}/igw/keyring
install -m 644 %{_saltceph}/igw/keyring/init.sls %{buildroot}/%{_saltceph}/igw/keyring

install -d -m 755 %{buildroot}/%{_saltceph}/igw/sysconfig
install -m 644 %{_saltceph}/igw/sysconfig/default.sls %{buildroot}/%{_saltceph}/igw/sysconfig
install -m 644 %{_saltceph}/igw/sysconfig/init.sls %{buildroot}/%{_saltceph}/igw/sysconfig

install -d -m 755 %{buildroot}/%{_saltceph}/mds
install -m 644 %{_saltceph}/mds/default.sls %{buildroot}/%{_saltceph}/mds
install -m 644 %{_saltceph}/mds/init.sls %{buildroot}/%{_saltceph}/mds

install -d -m 755 %{buildroot}/%{_saltceph}/mds/key
install -m 644 %{_saltceph}/mds/key/default.sls %{buildroot}/%{_saltceph}/mds/key
install -m 644 %{_saltceph}/mds/key/init.sls %{buildroot}/%{_saltceph}/mds/key
install -m 644 %{_saltceph}/mds/key/shared.sls %{buildroot}/%{_saltceph}/mds/key

install -d -m 755 %{buildroot}/%{_saltceph}/mds/auth
install -m 644 %{_saltceph}/mds/auth/default.sls %{buildroot}/%{_saltceph}/mds/auth
install -m 644 %{_saltceph}/mds/auth/init.sls %{buildroot}/%{_saltceph}/mds/auth
install -m 644 %{_saltceph}/mds/auth/shared.sls %{buildroot}/%{_saltceph}/mds/auth

install -d -m 755 %{buildroot}/%{_saltceph}/mds/keyring
install -m 644 %{_saltceph}/mds/keyring/default.sls %{buildroot}/%{_saltceph}/mds/keyring
install -m 644 %{_saltceph}/mds/keyring/init.sls %{buildroot}/%{_saltceph}/mds/keyring

install -d -m 755 %{buildroot}/%{_saltceph}/mds/pools
install -m 644 %{_saltceph}/mds/pools/default.sls %{buildroot}/%{_saltceph}/mds/pools
install -m 644 %{_saltceph}/mds/pools/init.sls %{buildroot}/%{_saltceph}/mds/pools

install -d -m 755 %{buildroot}/%{_saltceph}/mds/files
install -m 644 %{_saltceph}/mds/files/keyring.j2 %{buildroot}/%{_saltceph}/mds/files

install -d -m 755 %{buildroot}/%{_saltceph}/mine_functions
install -m 644 %{_saltceph}/mine_functions/init.sls %{buildroot}/%{_saltceph}/mine_functions
install -d -m 755 %{buildroot}/%{_saltceph}/mine_functions/files
install -m 644 %{_saltceph}/mine_functions/files/mine_functions.conf %{buildroot}/%{_saltceph}/mine_functions/files

install -d -m 755 %{buildroot}/%{_saltceph}/mon
install -m 644 %{_saltceph}/mon/default.sls %{buildroot}/%{_saltceph}/mon
install -m 644 %{_saltceph}/mon/init.sls %{buildroot}/%{_saltceph}/mon

install -d -m 755 %{buildroot}/%{_saltceph}/mon/key
install -m 644 %{_saltceph}/mon/key/default.sls %{buildroot}/%{_saltceph}/mon/key
install -m 644 %{_saltceph}/mon/key/init.sls %{buildroot}/%{_saltceph}/mon/key


install -d -m 755 %{buildroot}/%{_saltceph}/mon/files
install -m 644 %{_saltceph}/mon/files/keyring.j2 %{buildroot}/%{_saltceph}/mon/files

install -d -m 755 %{buildroot}/%{_saltceph}/openattic
install -m 644 %{_saltceph}/openattic/authtool.sls %{buildroot}/%{_saltceph}/openattic

install -d -m 755 %{buildroot}/%{_saltceph}/openattic/files
install -m 644 %{_saltceph}/openattic/files/keyring.j2 %{buildroot}/%{_saltceph}/openattic/files/keyring.j2
install -m 644 %{_saltceph}/openattic/init.sls %{buildroot}/%{_saltceph}/openattic
install -m 644 %{_saltceph}/openattic/keyring.sls %{buildroot}/%{_saltceph}/openattic
install -m 644 %{_saltceph}/openattic/openattic.sls %{buildroot}/%{_saltceph}/openattic

install -d -m 755 %{buildroot}/%{_saltceph}/osd
install -m 644 %{_saltceph}/osd/default.sls %{buildroot}/%{_saltceph}/osd
install -m 644 %{_saltceph}/osd/init.sls %{buildroot}/%{_saltceph}/osd

install -d -m 755 %{buildroot}/%{_saltceph}/osd/key
install -m 644 %{_saltceph}/osd/key/default.sls %{buildroot}/%{_saltceph}/osd/key
install -m 644 %{_saltceph}/osd/key/init.sls %{buildroot}/%{_saltceph}/osd/key

install -d -m 755 %{buildroot}/%{_saltceph}/osd/auth
install -m 644 %{_saltceph}/osd/auth/default.sls %{buildroot}/%{_saltceph}/osd/auth
install -m 644 %{_saltceph}/osd/auth/init.sls %{buildroot}/%{_saltceph}/osd/auth

install -d -m 755 %{buildroot}/%{_saltceph}/osd/keyring
install -m 644 %{_saltceph}/osd/keyring/default.sls %{buildroot}/%{_saltceph}/osd/keyring
install -m 644 %{_saltceph}/osd/keyring/init.sls %{buildroot}/%{_saltceph}/osd/keyring

install -d -m 755 %{buildroot}/%{_saltceph}/osd/partition
install -m 644 %{_saltceph}/osd/partition/default.sls %{buildroot}/%{_saltceph}/osd/partition
install -m 644 %{_saltceph}/osd/partition/init.sls %{buildroot}/%{_saltceph}/osd/partition

install -d -m 755 %{buildroot}/%{_saltceph}/osd/scheduler
install -m 644 %{_saltceph}/osd/scheduler/default.sls %{buildroot}/%{_saltceph}/osd/scheduler
install -m 644 %{_saltceph}/osd/scheduler/init.sls %{buildroot}/%{_saltceph}/osd/scheduler


install -d -m 755 %{buildroot}/%{_saltceph}/osd/files
install -m 644 %{_saltceph}/osd/files/keyring.j2 %{buildroot}/%{_saltceph}/osd/files

install -d -m 755 %{buildroot}/%{_saltceph}/packages
install -m 644 %{_saltceph}/packages/custom-salt.sls %{buildroot}/%{_saltceph}/packages
install -m 644 %{_saltceph}/packages/default.sls %{buildroot}/%{_saltceph}/packages
install -m 644 %{_saltceph}/packages/init.sls %{buildroot}/%{_saltceph}/packages

install -d -m 755 %{buildroot}/%{_saltceph}/pool
install -m 644 %{_saltceph}/pool/custom.sls %{buildroot}/%{_saltceph}/pool
install -m 644 %{_saltceph}/pool/default.sls %{buildroot}/%{_saltceph}/pool
install -m 644 %{_saltceph}/pool/init.sls %{buildroot}/%{_saltceph}/pool

install -d -m 755 %{buildroot}/%{_saltceph}/reactor
install -m 644 %{_saltceph}/reactor/all_stages.sls %{buildroot}/%{_saltceph}/reactor
install -m 644 %{_saltceph}/reactor/discovery.sls %{buildroot}/%{_saltceph}/reactor
install -m 644 %{_saltceph}/reactor/highstate.sls %{buildroot}/%{_saltceph}/reactor
install -m 644 %{_saltceph}/reactor/initialize.sls %{buildroot}/%{_saltceph}/reactor
install -m 644 %{_saltceph}/reactor/master.sls %{buildroot}/%{_saltceph}/reactor
install -m 644 %{_saltceph}/reactor/prep_begin.sls %{buildroot}/%{_saltceph}/reactor
install -m 644 %{_saltceph}/reactor/prep_complete.sls %{buildroot}/%{_saltceph}/reactor
install -m 644 %{_saltceph}/reactor/prep_minion.sls %{buildroot}/%{_saltceph}/reactor

install -d -m 755 %{buildroot}/%{_saltceph}/refresh
install -m 644 %{_saltceph}/refresh/init.sls %{buildroot}/%{_saltceph}/refresh

install -d -m 755 %{buildroot}/%{_saltceph}/repo
install -m 644 %{_saltceph}/repo/custom.sls %{buildroot}/%{_saltceph}/repo
install -m 644 %{_saltceph}/repo/default.sls %{buildroot}/%{_saltceph}/repo
install -m 644 %{_saltceph}/repo/init.sls %{buildroot}/%{_saltceph}/repo

install -d -m 755 %{buildroot}/%{_saltceph}/rgw
install -m 644 %{_saltceph}/rgw/default.sls %{buildroot}/%{_saltceph}/rgw
install -m 644 %{_saltceph}/rgw/init.sls %{buildroot}/%{_saltceph}/rgw

install -d -m 755 %{buildroot}/%{_saltceph}/rgw/key
install -m 644 %{_saltceph}/rgw/key/default.sls %{buildroot}/%{_saltceph}/rgw/key
install -m 644 %{_saltceph}/rgw/key/init.sls %{buildroot}/%{_saltceph}/rgw/key
install -m 644 %{_saltceph}/rgw/key/shared.sls %{buildroot}/%{_saltceph}/rgw/key

install -d -m 755 %{buildroot}/%{_saltceph}/rgw/auth
install -m 644 %{_saltceph}/rgw/auth/default.sls %{buildroot}/%{_saltceph}/rgw/auth
install -m 644 %{_saltceph}/rgw/auth/init.sls %{buildroot}/%{_saltceph}/rgw/auth
install -m 644 %{_saltceph}/rgw/auth/shared.sls %{buildroot}/%{_saltceph}/rgw/auth

install -d -m 755 %{buildroot}/%{_saltceph}/rgw/keyring
install -m 644 %{_saltceph}/rgw/keyring/default.sls %{buildroot}/%{_saltceph}/rgw/keyring
install -m 644 %{_saltceph}/rgw/keyring/init.sls %{buildroot}/%{_saltceph}/rgw/keyring

install -d -m 755 %{buildroot}/%{_saltceph}/rgw/files
install -m 644 %{_saltceph}/rgw/files/rgw.j2 %{buildroot}/%{_saltceph}/rgw/files

install -d -m 755 %{buildroot}/%{_saltceph}/stage
install -m 644 %{_saltceph}/stage/all.sls %{buildroot}/%{_saltceph}/stage
install -m 644 %{_saltceph}/stage/benchmark.sls %{buildroot}/%{_saltceph}/stage
install -m 644 %{_saltceph}/stage/cephfs.sls %{buildroot}/%{_saltceph}/stage
install -m 644 %{_saltceph}/stage/configure.sls %{buildroot}/%{_saltceph}/stage

install -d -m 755 %{buildroot}/%{_saltceph}/stage/configure
install -m 644 %{_saltceph}/stage/configure/default.sls %{buildroot}/%{_saltceph}/stage/configure
install -m 644 %{_saltceph}/stage/deploy.sls %{buildroot}/%{_saltceph}/stage
install -m 644 %{_saltceph}/stage/discovery.sls %{buildroot}/%{_saltceph}/stage

install -d -m 755 %{buildroot}/%{_saltceph}/stage/discovery
install -m 644 %{_saltceph}/stage/discovery/custom.sls %{buildroot}/%{_saltceph}/stage/discovery
install -m 644 %{_saltceph}/stage/discovery/default.sls %{buildroot}/%{_saltceph}/stage/discovery
install -m 644 %{_saltceph}/stage/iscsi.sls %{buildroot}/%{_saltceph}/stage
install -m 644 %{_saltceph}/stage/prep.sls %{buildroot}/%{_saltceph}/stage

install -d -m 755 %{buildroot}/%{_saltceph}/stage/prep
install -m 644 %{_saltceph}/stage/prep/default.sls %{buildroot}/%{_saltceph}/stage/prep
install -m 644 %{_saltceph}/stage/prep_minions.sls %{buildroot}/%{_saltceph}/stage
install -m 644 %{_saltceph}/stage/removal.sls %{buildroot}/%{_saltceph}/stage
install -m 644 %{_saltceph}/stage/rgw.sls %{buildroot}/%{_saltceph}/stage
install -m 644 %{_saltceph}/stage/services.sls %{buildroot}/%{_saltceph}/stage

install -d -m 755 %{buildroot}/%{_saltceph}/sync
install -m 644 %{_saltceph}/sync/init.sls %{buildroot}/%{_saltceph}/sync

install -d -m 755 %{buildroot}/%{_saltceph}/time
install -m 644 %{_saltceph}/time/custom-salt.sls %{buildroot}/%{_saltceph}/time
install -m 644 %{_saltceph}/time/custom.sls %{buildroot}/%{_saltceph}/time
install -m 644 %{_saltceph}/time/init.sls %{buildroot}/%{_saltceph}/time
install -m 644 %{_saltceph}/time/ntp.sls %{buildroot}/%{_saltceph}/time

install -d -m 755 %{buildroot}/%{_saltceph}/updates
install -m 644 %{_saltceph}/updates/default.sls %{buildroot}/%{_saltceph}/updates
install -m 644 %{_saltceph}/updates/init.sls %{buildroot}/%{_saltceph}/updates
install -m 644 %{_saltceph}/updates/restart.sls %{buildroot}/%{_saltceph}/updates

install -m 644 srv/salt/top.sls %{buildroot}/srv/salt

cd %{buildroot}/%{_saltceph}/stage && ln -sf prep.sls 0.sls
cd %{buildroot}/%{_saltceph}/stage && ln -sf discovery.sls 1.sls
cd %{buildroot}/%{_saltceph}/stage && ln -sf configure.sls 2.sls
cd %{buildroot}/%{_saltceph}/stage && ln -sf deploy.sls 3.sls
cd %{buildroot}/%{_saltceph}/stage && ln -sf services.sls 4.sls

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
%dir /%{_runners}
%dir /%{_pillar}
%dir %attr(0755, salt, salt) /%{_pillar}/ceph
%dir %attr(0755, salt, salt) /%{_pillar}/ceph/stack
%dir /srv/modules
%dir /srv/modules/pillar
%dir /srv/salt/_modules
%dir %attr(0755, salt, salt) /%{_saltceph}
%dir /%{_saltceph}/admin
%dir /%{_saltceph}/admin/files
%dir /%{_saltceph}/admin/key
%dir /%{_saltceph}/configuration
%dir /%{_saltceph}/configuration/files
%dir /%{_saltceph}/events
%dir /%{_saltceph}/igw
%dir /%{_saltceph}/igw/files
%dir /%{_saltceph}/igw/import
%dir /%{_saltceph}/igw/key
%dir /%{_saltceph}/igw/auth
%dir /%{_saltceph}/igw/keyring
%dir /%{_saltceph}/igw/sysconfig
%dir /%{_saltceph}/mds
%dir /%{_saltceph}/mds/files
%dir /%{_saltceph}/mds/key
%dir /%{_saltceph}/mds/auth
%dir /%{_saltceph}/mds/keyring
%dir /%{_saltceph}/mds/pools
%dir /%{_saltceph}/mine_functions
%dir /%{_saltceph}/mine_functions/files
%dir /%{_saltceph}/mon
%dir /%{_saltceph}/mon/files
%dir /%{_saltceph}/mon/key
%dir /%{_saltceph}/openattic
%dir /%{_saltceph}/openattic/files
%dir /%{_saltceph}/osd
%dir /%{_saltceph}/osd/files
%dir /%{_saltceph}/osd/key
%dir /%{_saltceph}/osd/auth
%dir /%{_saltceph}/osd/keyring
%dir /%{_saltceph}/osd/partition
%dir /%{_saltceph}/osd/scheduler
%dir /%{_saltceph}/packages
%dir /%{_saltceph}/pool
%dir /%{_saltceph}/reactor
%dir /%{_saltceph}/refresh
%dir /%{_saltceph}/repo
%dir /%{_saltceph}/rgw
%dir /%{_saltceph}/rgw/files
%dir /%{_saltceph}/rgw/key
%dir /%{_saltceph}/rgw/auth
%dir /%{_saltceph}/rgw/keyring
%dir /%{_saltceph}/stage
%dir /%{_saltceph}/stage/configure
%dir /%{_saltceph}/stage/discovery
%dir /%{_saltceph}/stage/prep
%dir /%{_saltceph}/sync
%dir /%{_saltceph}/time
%dir /%{_saltceph}/updates
%config(noreplace) /etc/salt/master.d/*.conf
%config /%{_runners}/*.py
%config /%{_pillar}/top.sls
/%{_pillar}/ceph/README
%config /%{_pillar}/ceph/init.sls
%config(noreplace) /%{_pillar}/ceph/master_minion.sls
%config /%{_pillar}/ceph/stack/stack.cfg
%config /srv/salt/top.sls
%config /srv/salt/_modules/*.py
%config /%{_saltceph}/admin/*.sls
%config /%{_saltceph}/admin/files/*.j2
%config /%{_saltceph}/admin/key/*.sls
%config /%{_saltceph}/configuration/*.sls
%config /%{_saltceph}/configuration/files/*.j2
%config /%{_saltceph}/events/*.sls
%config /%{_saltceph}/igw/*.sls
%config /%{_saltceph}/igw/files/*.j2
%config /%{_saltceph}/igw/import/*.sls
%config /%{_saltceph}/igw/key/*.sls
%config /%{_saltceph}/igw/auth/*.sls
%config /%{_saltceph}/igw/keyring/*.sls
%config /%{_saltceph}/igw/sysconfig/*.sls
%config /%{_saltceph}/mds/*.sls
%config /%{_saltceph}/mds/files/*.j2
%config /%{_saltceph}/mds/key/*.sls
%config /%{_saltceph}/mds/auth/*.sls
%config /%{_saltceph}/mds/keyring/*.sls
%config /%{_saltceph}/mds/pools/*.sls
%config /%{_saltceph}/mine_functions/*.sls
%config /%{_saltceph}/mine_functions/files/*.conf
%config /%{_saltceph}/mon/*.sls
%config /%{_saltceph}/mon/files/*.j2
%config /%{_saltceph}/mon/key/*.sls
%config /%{_saltceph}/openattic/*.sls
%config /%{_saltceph}/openattic/files/*.j2
%config /%{_saltceph}/osd/*.sls
%config /%{_saltceph}/osd/files/*.j2
%config /%{_saltceph}/osd/key/*.sls
%config /%{_saltceph}/osd/auth/*.sls
%config /%{_saltceph}/osd/keyring/*.sls
%config /%{_saltceph}/osd/partition/*.sls
%config /%{_saltceph}/osd/scheduler/*.sls
%config /%{_saltceph}/packages/*.sls
%config /%{_saltceph}/pool/*.sls
%config /%{_saltceph}/reactor/*.sls
%config /%{_saltceph}/refresh/*.sls
%config /%{_saltceph}/repo/*.sls
%config /%{_saltceph}/rgw/*.sls
%config /%{_saltceph}/rgw/files/*.j2
%config /%{_saltceph}/rgw/key/*.sls
%config /%{_saltceph}/rgw/auth/*.sls
%config /%{_saltceph}/rgw/keyring/*.sls
%config /%{_saltceph}/stage/*.sls
%config /%{_saltceph}/stage/configure/*.sls
%config /%{_saltceph}/stage/discovery/*.sls
%config /%{_saltceph}/stage/prep/*.sls
%config /%{_saltceph}/sync/*.sls
%config /%{_saltceph}/time/*.sls
%config /%{_saltceph}/updates/*.sls
%doc
%dir %attr(-, root, root) %{_docdir}/%{name}
%{_docdir}/%{name}/*


%changelog
* Thu Sep  8 2016 Eric Jackson
- 
