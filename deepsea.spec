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
Version:        0.6
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
install -m 644 %{_runners}/advise.py %{buildroot}/%{_runners}
install -m 644 %{_runners}/check.py %{buildroot}/%{_runners}
install -m 644 %{_runners}/configure.py %{buildroot}/%{_runners}
install -m 644 %{_runners}/filequeue.py %{buildroot}/%{_runners}
install -m 644 %{_runners}/minions.py %{buildroot}/%{_runners}
install -m 644 %{_runners}/populate.py %{buildroot}/%{_runners}
install -m 644 %{_runners}/rescinded.py %{buildroot}/%{_runners}
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
install -m 644 srv/salt/_modules/advise.py %{buildroot}/srv/salt/_modules
install -m 644 srv/salt/_modules/keyring.py %{buildroot}/srv/salt/_modules
install -m 644 srv/salt/_modules/cephdisks.py %{buildroot}/srv/salt/_modules
install -m 644 srv/salt/_modules/freedisks.py %{buildroot}/srv/salt/_modules
install -m 644 srv/salt/_modules/mon.py %{buildroot}/srv/salt/_modules
install -m 644 srv/salt/_modules/osd.py %{buildroot}/srv/salt/_modules
install -m 644 srv/salt/_modules/retry.py %{buildroot}/srv/salt/_modules
install -m 644 srv/salt/_modules/rgw.py %{buildroot}/srv/salt/_modules
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
install -m 644 %{_saltceph}/configuration/shared.sls %{buildroot}/%{_saltceph}/configuration

install -d -m 755 %{buildroot}/%{_saltceph}/configuration/check
install -m 644 %{_saltceph}/configuration/check/default.sls %{buildroot}/%{_saltceph}/configuration/check
install -m 644 %{_saltceph}/configuration/check/init.sls %{buildroot}/%{_saltceph}/configuration/check

install -d -m 755 %{buildroot}/%{_saltceph}/configuration/files
install -m 644 %{_saltceph}/configuration/files/ceph.conf.j2 %{buildroot}/%{_saltceph}/configuration/files
install -m 644 %{_saltceph}/configuration/files/ceph.conf-shared.j2 %{buildroot}/%{_saltceph}/configuration/files
install -m 644 %{_saltceph}/configuration/files/ceph.conf.rgw %{buildroot}/%{_saltceph}/configuration/files


install -d -m 755 %{buildroot}/%{_saltceph}/events
install -m 644 %{_saltceph}/events/begin_prep.sls %{buildroot}/%{_saltceph}/events
install -m 644 %{_saltceph}/events/complete_prep.sls %{buildroot}/%{_saltceph}/events

install -d -m 755 %{buildroot}/%{_saltceph}/igw
install -m 644 %{_saltceph}/igw/default.sls %{buildroot}/%{_saltceph}/igw
install -m 644 %{_saltceph}/igw/init.sls %{buildroot}/%{_saltceph}/igw

install -d -m 755 %{buildroot}/%{_saltceph}/igw/files
install -m 644 %{_saltceph}/igw/files/sysconfig.lrbd.j2 %{buildroot}/%{_saltceph}/igw/files
install -m 644 %{_saltceph}/igw/files/keyring.j2 %{buildroot}/%{_saltceph}/igw/files
install -m 644 %{_saltceph}/igw/files/lrbd.conf.j2 %{buildroot}/%{_saltceph}/igw/files

install -d -m 755 %{buildroot}/%{_saltceph}/igw/config
install -m 644 %{_saltceph}/igw/config/default.sls %{buildroot}/%{_saltceph}/igw/config
install -m 644 %{_saltceph}/igw/config/init.sls %{buildroot}/%{_saltceph}/igw/config

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
install -m 644 %{_saltceph}/igw/keyring/shared.sls %{buildroot}/%{_saltceph}/igw/keyring

install -d -m 755 %{buildroot}/%{_saltceph}/igw/sysconfig
install -m 644 %{_saltceph}/igw/sysconfig/default.sls %{buildroot}/%{_saltceph}/igw/sysconfig
install -m 644 %{_saltceph}/igw/sysconfig/init.sls %{buildroot}/%{_saltceph}/igw/sysconfig
install -m 644 %{_saltceph}/igw/sysconfig/shared.sls %{buildroot}/%{_saltceph}/igw/sysconfig

install -d -m 755 %{buildroot}/%{_saltceph}/mds
install -m 644 %{_saltceph}/mds/default.sls %{buildroot}/%{_saltceph}/mds
install -m 644 %{_saltceph}/mds/init.sls %{buildroot}/%{_saltceph}/mds
install -m 644 %{_saltceph}/mds/shared.sls %{buildroot}/%{_saltceph}/mds

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
install -m 644 %{_saltceph}/mds/keyring/shared.sls %{buildroot}/%{_saltceph}/mds/keyring

install -d -m 755 %{buildroot}/%{_saltceph}/mds/pools
install -m 644 %{_saltceph}/mds/pools/default.sls %{buildroot}/%{_saltceph}/mds/pools
install -m 644 %{_saltceph}/mds/pools/init.sls %{buildroot}/%{_saltceph}/mds/pools

install -d -m 755 %{buildroot}/%{_saltceph}/mds/files
install -m 644 %{_saltceph}/mds/files/keyring.j2 %{buildroot}/%{_saltceph}/mds/files

install -d -m 755 %{buildroot}/%{_saltceph}/mines
install -m 644 %{_saltceph}/mines/default.sls %{buildroot}/%{_saltceph}/mines
install -m 644 %{_saltceph}/mines/init.sls %{buildroot}/%{_saltceph}/mines

install -d -m 755 %{buildroot}/%{_saltceph}/mines/files
install -m 644 %{_saltceph}/mines/files/mine_functions.conf %{buildroot}/%{_saltceph}/mines/files

install -d -m 755 %{buildroot}/%{_saltceph}/mon
install -m 644 %{_saltceph}/mon/default.sls %{buildroot}/%{_saltceph}/mon
install -m 644 %{_saltceph}/mon/init.sls %{buildroot}/%{_saltceph}/mon

install -d -m 755 %{buildroot}/%{_saltceph}/mon/key
install -m 644 %{_saltceph}/mon/key/default.sls %{buildroot}/%{_saltceph}/mon/key
install -m 644 %{_saltceph}/mon/key/init.sls %{buildroot}/%{_saltceph}/mon/key


install -d -m 755 %{buildroot}/%{_saltceph}/mon/files
install -m 644 %{_saltceph}/mon/files/keyring.j2 %{buildroot}/%{_saltceph}/mon/files

install -d -m 755 %{buildroot}/%{_saltceph}/openattic
install -m 644 %{_saltceph}/openattic/default.sls %{buildroot}/%{_saltceph}/openattic
install -m 644 %{_saltceph}/openattic/init.sls %{buildroot}/%{_saltceph}/openattic

install -d -m 755 %{buildroot}/%{_saltceph}/openattic/auth
install -m 644 %{_saltceph}/openattic/auth/default.sls %{buildroot}/%{_saltceph}/openattic/auth/
install -m 644 %{_saltceph}/openattic/auth/init.sls %{buildroot}/%{_saltceph}/openattic/auth/

install -d -m 755 %{buildroot}/%{_saltceph}/openattic/files
install -m 644 %{_saltceph}/openattic/files/keyring.j2 %{buildroot}/%{_saltceph}/openattic/files/keyring.j2

install -d -m 755 %{buildroot}/%{_saltceph}/openattic/key
install -m 644 %{_saltceph}/openattic/key/default.sls %{buildroot}/%{_saltceph}/openattic/key/
install -m 644 %{_saltceph}/openattic/key/init.sls %{buildroot}/%{_saltceph}/openattic/key/

install -d -m 755 %{buildroot}/%{_saltceph}/openattic/keyring
install -m 644 %{_saltceph}/openattic/keyring/default.sls %{buildroot}/%{_saltceph}/openattic/keyring/
install -m 644 %{_saltceph}/openattic/keyring/init.sls %{buildroot}/%{_saltceph}/openattic/keyring/

install -d -m 755 %{buildroot}/%{_saltceph}/openattic/oaconfig
install -m 644 %{_saltceph}/openattic/oaconfig/default.sls %{buildroot}/%{_saltceph}/openattic/oaconfig/
install -m 644 %{_saltceph}/openattic/oaconfig/init.sls %{buildroot}/%{_saltceph}/openattic/oaconfig/

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

install -d -m 755 %{buildroot}/%{_saltceph}/packages/common
install -m 644 %{_saltceph}/packages/common/default.sls %{buildroot}/%{_saltceph}/packages/common
install -m 644 %{_saltceph}/packages/common/init.sls %{buildroot}/%{_saltceph}/packages/common

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
install -m 644 %{_saltceph}/refresh/default.sls %{buildroot}/%{_saltceph}/refresh
install -m 644 %{_saltceph}/refresh/init.sls %{buildroot}/%{_saltceph}/refresh

install -d -m 755 %{buildroot}/%{_saltceph}/remove

install -d -m 755 %{buildroot}/%{_saltceph}/remove/igw/auth
install -m 644 %{_saltceph}/remove/igw/auth/init.sls %{buildroot}/%{_saltceph}/remove/igw/auth
install -m 644 %{_saltceph}/remove/igw/auth/default.sls %{buildroot}/%{_saltceph}/remove/igw/auth

install -d -m 755 %{buildroot}/%{_saltceph}/remove/mds
install -m 644 %{_saltceph}/remove/mds/init.sls %{buildroot}/%{_saltceph}/remove/mds
install -m 644 %{_saltceph}/remove/mds/default.sls %{buildroot}/%{_saltceph}/remove/mds

install -d -m 755 %{buildroot}/%{_saltceph}/remove/mon
install -m 644 %{_saltceph}/remove/mon/init.sls %{buildroot}/%{_saltceph}/remove/mon
install -m 644 %{_saltceph}/remove/mon/default.sls %{buildroot}/%{_saltceph}/remove/mon

install -d -m 755 %{buildroot}/%{_saltceph}/remove/rgw
install -m 644 %{_saltceph}/remove/rgw/init.sls %{buildroot}/%{_saltceph}/remove/rgw
install -m 644 %{_saltceph}/remove/rgw/default.sls %{buildroot}/%{_saltceph}/remove/rgw

install -d -m 755 %{buildroot}/%{_saltceph}/remove/storage
install -m 644 %{_saltceph}/remove/storage/init.sls %{buildroot}/%{_saltceph}/remove/storage
install -m 644 %{_saltceph}/remove/storage/default.sls %{buildroot}/%{_saltceph}/remove/storage

install -d -m 755 %{buildroot}/%{_saltceph}/rescind
install -m 644 %{_saltceph}/rescind/init.sls %{buildroot}/%{_saltceph}/rescind
install -m 644 %{_saltceph}/rescind/default.sls %{buildroot}/%{_saltceph}/rescind
install -m 644 %{_saltceph}/rescind/nop.sls %{buildroot}/%{_saltceph}/rescind

install -d -m 755 %{buildroot}/%{_saltceph}/rescind/admin
install -m 644 %{_saltceph}/rescind/admin/init.sls %{buildroot}/%{_saltceph}/rescind/admin
install -m 644 %{_saltceph}/rescind/admin/default.sls %{buildroot}/%{_saltceph}/rescind/admin

install -d -m 755 %{buildroot}/%{_saltceph}/rescind/igw-client
install -m 644 %{_saltceph}/rescind/igw-client/init.sls %{buildroot}/%{_saltceph}/rescind/igw-client
install -m 644 %{_saltceph}/rescind/igw-client/default.sls %{buildroot}/%{_saltceph}/rescind/igw-client

install -d -m 755 %{buildroot}/%{_saltceph}/rescind/igw
install -m 644 %{_saltceph}/rescind/igw/init.sls %{buildroot}/%{_saltceph}/rescind/igw
install -m 644 %{_saltceph}/rescind/igw/default.sls %{buildroot}/%{_saltceph}/rescind/igw

install -d -m 755 %{buildroot}/%{_saltceph}/rescind/igw/keyring
install -m 644 %{_saltceph}/rescind/igw/keyring/init.sls %{buildroot}/%{_saltceph}/rescind/igw/keyring
install -m 644 %{_saltceph}/rescind/igw/keyring/default.sls %{buildroot}/%{_saltceph}/rescind/igw/keyring

install -d -m 755 %{buildroot}/%{_saltceph}/rescind/igw/lrbd
install -m 644 %{_saltceph}/rescind/igw/lrbd/init.sls %{buildroot}/%{_saltceph}/rescind/igw/lrbd
install -m 644 %{_saltceph}/rescind/igw/lrbd/default.sls %{buildroot}/%{_saltceph}/rescind/igw/lrbd

install -d -m 755 %{buildroot}/%{_saltceph}/rescind/igw/sysconfig
install -m 644 %{_saltceph}/rescind/igw/sysconfig/init.sls %{buildroot}/%{_saltceph}/rescind/igw/sysconfig
install -m 644 %{_saltceph}/rescind/igw/sysconfig/default.sls %{buildroot}/%{_saltceph}/rescind/igw/sysconfig

install -d -m 755 %{buildroot}/%{_saltceph}/rescind/master
install -m 644 %{_saltceph}/rescind/master/init.sls %{buildroot}/%{_saltceph}/rescind/master
install -m 644 %{_saltceph}/rescind/master/default.sls %{buildroot}/%{_saltceph}/rescind/master

install -d -m 755 %{buildroot}/%{_saltceph}/rescind/mds-client
install -m 644 %{_saltceph}/rescind/mds-client/init.sls %{buildroot}/%{_saltceph}/rescind/mds-client
install -m 644 %{_saltceph}/rescind/mds-client/default.sls %{buildroot}/%{_saltceph}/rescind/mds-client

install -d -m 755 %{buildroot}/%{_saltceph}/rescind/mds-nfs
install -m 644 %{_saltceph}/rescind/mds-nfs/init.sls %{buildroot}/%{_saltceph}/rescind/mds-nfs
install -m 644 %{_saltceph}/rescind/mds-nfs/default.sls %{buildroot}/%{_saltceph}/rescind/mds-nfs

install -d -m 755 %{buildroot}/%{_saltceph}/rescind/mds
install -m 644 %{_saltceph}/rescind/mds/init.sls %{buildroot}/%{_saltceph}/rescind/mds
install -m 644 %{_saltceph}/rescind/mds/default.sls %{buildroot}/%{_saltceph}/rescind/mds

install -d -m 755 %{buildroot}/%{_saltceph}/rescind/mds/keyring
install -m 644 %{_saltceph}/rescind/mds/keyring/init.sls %{buildroot}/%{_saltceph}/rescind/mds/keyring
install -m 644 %{_saltceph}/rescind/mds/keyring/default.sls %{buildroot}/%{_saltceph}/rescind/mds/keyring

install -d -m 755 %{buildroot}/%{_saltceph}/rescind/mon
install -m 644 %{_saltceph}/rescind/mon/init.sls %{buildroot}/%{_saltceph}/rescind/mon
install -m 644 %{_saltceph}/rescind/mon/default.sls %{buildroot}/%{_saltceph}/rescind/mon

install -d -m 755 %{buildroot}/%{_saltceph}/rescind/admin
install -m 644 %{_saltceph}/rescind/admin/init.sls %{buildroot}/%{_saltceph}/rescind/admin
install -m 644 %{_saltceph}/rescind/admin/default.sls %{buildroot}/%{_saltceph}/rescind/admin

install -d -m 755 %{buildroot}/%{_saltceph}/rescind/rgw-client
install -m 644 %{_saltceph}/rescind/rgw-client/init.sls %{buildroot}/%{_saltceph}/rescind/rgw-client
install -m 644 %{_saltceph}/rescind/rgw-client/default.sls %{buildroot}/%{_saltceph}/rescind/rgw-client

install -d -m 755 %{buildroot}/%{_saltceph}/rescind/rgw-nfs
install -m 644 %{_saltceph}/rescind/rgw-nfs/init.sls %{buildroot}/%{_saltceph}/rescind/rgw-nfs
install -m 644 %{_saltceph}/rescind/rgw-nfs/default.sls %{buildroot}/%{_saltceph}/rescind/rgw-nfs

install -d -m 755 %{buildroot}/%{_saltceph}/rescind/rgw
install -m 644 %{_saltceph}/rescind/rgw/init.sls %{buildroot}/%{_saltceph}/rescind/rgw
install -m 644 %{_saltceph}/rescind/rgw/default.sls %{buildroot}/%{_saltceph}/rescind/rgw

install -d -m 755 %{buildroot}/%{_saltceph}/rescind/rgw/keyring
install -m 644 %{_saltceph}/rescind/rgw/keyring/init.sls %{buildroot}/%{_saltceph}/rescind/rgw/keyring
install -m 644 %{_saltceph}/rescind/rgw/keyring/default.sls %{buildroot}/%{_saltceph}/rescind/rgw/keyring

install -d -m 755 %{buildroot}/%{_saltceph}/rescind/storage
install -m 644 %{_saltceph}/rescind/storage/init.sls %{buildroot}/%{_saltceph}/rescind/storage
install -m 644 %{_saltceph}/rescind/storage/default.sls %{buildroot}/%{_saltceph}/rescind/storage

install -d -m 755 %{buildroot}/%{_saltceph}/rescind/storage/keyring
install -m 644 %{_saltceph}/rescind/storage/keyring/init.sls %{buildroot}/%{_saltceph}/rescind/storage/keyring
install -m 644 %{_saltceph}/rescind/storage/keyring/default.sls %{buildroot}/%{_saltceph}/rescind/storage/keyring

install -d -m 755 %{buildroot}/%{_saltceph}/repo
install -m 644 %{_saltceph}/repo/custom.sls %{buildroot}/%{_saltceph}/repo
install -m 644 %{_saltceph}/repo/default.sls %{buildroot}/%{_saltceph}/repo
install -m 644 %{_saltceph}/repo/init.sls %{buildroot}/%{_saltceph}/repo

install -d -m 755 %{buildroot}/%{_saltceph}/rgw
install -m 644 %{_saltceph}/rgw/default.sls %{buildroot}/%{_saltceph}/rgw
install -m 644 %{_saltceph}/rgw/init.sls %{buildroot}/%{_saltceph}/rgw
install -m 644 %{_saltceph}/rgw/shared.sls %{buildroot}/%{_saltceph}/rgw

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
install -m 644 %{_saltceph}/rgw/keyring/shared.sls %{buildroot}/%{_saltceph}/rgw/keyring

install -d -m 755 %{buildroot}/%{_saltceph}/rgw/files
install -m 644 %{_saltceph}/rgw/files/rgw.j2 %{buildroot}/%{_saltceph}/rgw/files

install -d -m 755 %{buildroot}/%{_saltceph}/stage/all
install -m 644 %{_saltceph}/stage/all/default.sls %{buildroot}/%{_saltceph}/stage/all
install -m 644 %{_saltceph}/stage/all/init.sls %{buildroot}/%{_saltceph}/stage/all

install -d -m 755 %{buildroot}/%{_saltceph}/stage/benchmark
install -m 644 %{_saltceph}/stage/benchmark/default.sls %{buildroot}/%{_saltceph}/stage/benchmark
install -m 644 %{_saltceph}/stage/benchmark/init.sls %{buildroot}/%{_saltceph}/stage/benchmark

install -d -m 755 %{buildroot}/%{_saltceph}/stage/cephfs
install -m 644 %{_saltceph}/stage/cephfs/default.sls %{buildroot}/%{_saltceph}/stage/cephfs
install -m 644 %{_saltceph}/stage/cephfs/init.sls %{buildroot}/%{_saltceph}/stage/cephfs

install -d -m 755 %{buildroot}/%{_saltceph}/stage/configure
install -m 644 %{_saltceph}/stage/configure/default.sls %{buildroot}/%{_saltceph}/stage/configure
install -m 644 %{_saltceph}/stage/configure/init.sls %{buildroot}/%{_saltceph}/stage/configure

install -d -m 755 %{buildroot}/%{_saltceph}/stage/deploy
install -m 644 %{_saltceph}/stage/deploy/default.sls %{buildroot}/%{_saltceph}/stage/deploy
install -m 644 %{_saltceph}/stage/deploy/init.sls %{buildroot}/%{_saltceph}/stage/deploy

install -d -m 755 %{buildroot}/%{_saltceph}/stage/discovery
install -m 644 %{_saltceph}/stage/discovery/default.sls %{buildroot}/%{_saltceph}/stage/discovery
install -m 644 %{_saltceph}/stage/discovery/init.sls %{buildroot}/%{_saltceph}/stage/discovery

install -d -m 755 %{buildroot}/%{_saltceph}/stage/iscsi
install -m 644 %{_saltceph}/stage/iscsi/default.sls %{buildroot}/%{_saltceph}/stage/iscsi
install -m 644 %{_saltceph}/stage/iscsi/init.sls %{buildroot}/%{_saltceph}/stage/iscsi

install -d -m 755 %{buildroot}/%{_saltceph}/stage/openattic
install -m 644 %{_saltceph}/stage/openattic/default.sls %{buildroot}/%{_saltceph}/stage/openattic
install -m 644 %{_saltceph}/stage/openattic/init.sls %{buildroot}/%{_saltceph}/stage/openattic

install -d -m 755 %{buildroot}/%{_saltceph}/stage/prep
install -m 644 %{_saltceph}/stage/prep/default.sls %{buildroot}/%{_saltceph}/stage/prep
install -m 644 %{_saltceph}/stage/prep/init.sls %{buildroot}/%{_saltceph}/stage/prep

install -d -m 755 %{buildroot}/%{_saltceph}/stage/prep/master
install -m 644 %{_saltceph}/stage/prep/master/default.sls %{buildroot}/%{_saltceph}/stage/prep/master
install -m 644 %{_saltceph}/stage/prep/master/init.sls %{buildroot}/%{_saltceph}/stage/prep/master

install -d -m 755 %{buildroot}/%{_saltceph}/stage/prep/minion
install -m 644 %{_saltceph}/stage/prep/minion/default.sls %{buildroot}/%{_saltceph}/stage/prep/minion
install -m 644 %{_saltceph}/stage/prep/minion/init.sls %{buildroot}/%{_saltceph}/stage/prep/minion

install -d -m 755 %{buildroot}/%{_saltceph}/stage/removal
install -m 644 %{_saltceph}/stage/removal/default.sls %{buildroot}/%{_saltceph}/stage/removal
install -m 644 %{_saltceph}/stage/removal/init.sls %{buildroot}/%{_saltceph}/stage/removal

install -d -m 755 %{buildroot}/%{_saltceph}/stage/radosgw
install -m 644 %{_saltceph}/stage/radosgw/default.sls %{buildroot}/%{_saltceph}/stage/radosgw
install -m 644 %{_saltceph}/stage/radosgw/init.sls %{buildroot}/%{_saltceph}/stage/radosgw

install -d -m 755 %{buildroot}/%{_saltceph}/stage/services
install -m 644 %{_saltceph}/stage/services/default.sls %{buildroot}/%{_saltceph}/stage/services
install -m 644 %{_saltceph}/stage/services/init.sls %{buildroot}/%{_saltceph}/stage/services

install -d -m 755 %{buildroot}/%{_saltceph}/sync
install -m 644 %{_saltceph}/sync/default.sls %{buildroot}/%{_saltceph}/sync
install -m 644 %{_saltceph}/sync/init.sls %{buildroot}/%{_saltceph}/sync

install -d -m 755 %{buildroot}/%{_saltceph}/time
install -m 644 %{_saltceph}/time/default.sls %{buildroot}/%{_saltceph}/time
install -m 644 %{_saltceph}/time/init.sls %{buildroot}/%{_saltceph}/time

install -d -m 755 %{buildroot}/%{_saltceph}/time/ntp
install -m 644 %{_saltceph}/time/ntp/default.sls %{buildroot}/%{_saltceph}/time/ntp
install -m 644 %{_saltceph}/time/ntp/init.sls %{buildroot}/%{_saltceph}/time/ntp

install -d -m 755 %{buildroot}/%{_saltceph}/updates
install -m 644 %{_saltceph}/updates/default.sls %{buildroot}/%{_saltceph}/updates
install -m 644 %{_saltceph}/updates/init.sls %{buildroot}/%{_saltceph}/updates

install -d -m 755 %{buildroot}/%{_saltceph}/updates/restart
install -m 644 %{_saltceph}/updates/restart/default.sls %{buildroot}/%{_saltceph}/updates/restart
install -m 644 %{_saltceph}/updates/restart/init.sls %{buildroot}/%{_saltceph}/updates/restart


cd %{buildroot}/%{_saltceph}/stage && ln -sf prep 0
cd %{buildroot}/%{_saltceph}/stage && ln -sf discovery 1
cd %{buildroot}/%{_saltceph}/stage && ln -sf configure 2
cd %{buildroot}/%{_saltceph}/stage && ln -sf deploy 3
cd %{buildroot}/%{_saltceph}/stage && ln -sf services 4
cd %{buildroot}/%{_saltceph}/stage && ln -sf removal 5

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
%dir /%{_saltceph}/configuration/check
%dir /%{_saltceph}/events
%dir /%{_saltceph}/igw
%dir /%{_saltceph}/igw/config
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
%dir /%{_saltceph}/mines
%dir /%{_saltceph}/mines/files
%dir /%{_saltceph}/mon
%dir /%{_saltceph}/mon/files
%dir /%{_saltceph}/mon/key
%dir /%{_saltceph}/openattic
%dir /%{_saltceph}/openattic/auth
%dir /%{_saltceph}/openattic/files
%dir /%{_saltceph}/openattic/key
%dir /%{_saltceph}/openattic/keyring
%dir /%{_saltceph}/openattic/oaconfig
%dir /%{_saltceph}/osd
%dir /%{_saltceph}/osd/files
%dir /%{_saltceph}/osd/key
%dir /%{_saltceph}/osd/auth
%dir /%{_saltceph}/osd/keyring
%dir /%{_saltceph}/osd/partition
%dir /%{_saltceph}/osd/scheduler
%dir /%{_saltceph}/packages
%dir /%{_saltceph}/packages/common
%dir /%{_saltceph}/pool
%dir /%{_saltceph}/reactor
%dir /%{_saltceph}/refresh
%dir /%{_saltceph}/repo
%dir /%{_saltceph}/remove
%dir /%{_saltceph}/remove/igw
%dir /%{_saltceph}/remove/igw/auth
%dir /%{_saltceph}/remove/mon
%dir /%{_saltceph}/remove/mds
%dir /%{_saltceph}/remove/rgw
%dir /%{_saltceph}/remove/storage
%dir /%{_saltceph}/rescind
%dir /%{_saltceph}/rescind/admin
%dir /%{_saltceph}/rescind/igw-client
%dir /%{_saltceph}/rescind/igw
%dir /%{_saltceph}/rescind/igw/keyring
%dir /%{_saltceph}/rescind/igw/lrbd
%dir /%{_saltceph}/rescind/igw/sysconfig
%dir /%{_saltceph}/rescind/master
%dir /%{_saltceph}/rescind/mds-client
%dir /%{_saltceph}/rescind/mds-nfs
%dir /%{_saltceph}/rescind/mds
%dir /%{_saltceph}/rescind/mds/keyring
%dir /%{_saltceph}/rescind/mon
%dir /%{_saltceph}/rescind/rgw-client
%dir /%{_saltceph}/rescind/rgw-nfs
%dir /%{_saltceph}/rescind/rgw
%dir /%{_saltceph}/rescind/rgw/keyring
%dir /%{_saltceph}/rescind/storage
%dir /%{_saltceph}/rescind/storage/keyring
%dir /%{_saltceph}/rgw
%dir /%{_saltceph}/rgw/files
%dir /%{_saltceph}/rgw/key
%dir /%{_saltceph}/rgw/auth
%dir /%{_saltceph}/rgw/keyring
%dir /%{_saltceph}/stage
%dir /%{_saltceph}/stage/all
%dir /%{_saltceph}/stage/benchmark
%dir /%{_saltceph}/stage/cephfs
%dir /%{_saltceph}/stage/configure
%dir /%{_saltceph}/stage/deploy
%dir /%{_saltceph}/stage/discovery
%dir /%{_saltceph}/stage/iscsi
%dir /%{_saltceph}/stage/openattic
%dir /%{_saltceph}/stage/prep
%dir /%{_saltceph}/stage/prep/master
%dir /%{_saltceph}/stage/prep/minion
%dir /%{_saltceph}/stage/radosgw
%dir /%{_saltceph}/stage/removal
%dir /%{_saltceph}/stage/services
%dir /%{_saltceph}/sync
%dir /%{_saltceph}/time
%dir /%{_saltceph}/time/ntp
%dir /%{_saltceph}/updates
%dir /%{_saltceph}/updates/restart
%config(noreplace) /etc/salt/master.d/*.conf
%config /%{_runners}/*.py
%config /%{_pillar}/top.sls
/%{_pillar}/ceph/README
%config /%{_pillar}/ceph/init.sls
%config(noreplace) /%{_pillar}/ceph/master_minion.sls
%config /%{_pillar}/ceph/stack/stack.cfg
%config /srv/salt/_modules/*.py
%config /%{_saltceph}/admin/*.sls
%config /%{_saltceph}/admin/files/*.j2
%config /%{_saltceph}/admin/key/*.sls
%config /%{_saltceph}/configuration/*.sls
%config /%{_saltceph}/configuration/check/*.sls
%config /%{_saltceph}/configuration/files/ceph.conf*
%config /%{_saltceph}/events/*.sls
%config /%{_saltceph}/igw/*.sls
%config /%{_saltceph}/igw/files/*.j2
%config /%{_saltceph}/igw/config/*.sls
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
%config /%{_saltceph}/mines/*.sls
%config /%{_saltceph}/mines/files/*.conf
%config /%{_saltceph}/mon/*.sls
%config /%{_saltceph}/mon/files/*.j2
%config /%{_saltceph}/mon/key/*.sls
%config /%{_saltceph}/openattic/*.sls
%config /%{_saltceph}/openattic/auth/*.sls
%config /%{_saltceph}/openattic/key/*.sls
%config /%{_saltceph}/openattic/keyring/*.sls
%config /%{_saltceph}/openattic/oaconfig/*.sls
%config /%{_saltceph}/openattic/files/*.j2
%config /%{_saltceph}/osd/*.sls
%config /%{_saltceph}/osd/files/*.j2
%config /%{_saltceph}/osd/key/*.sls
%config /%{_saltceph}/osd/auth/*.sls
%config /%{_saltceph}/osd/keyring/*.sls
%config /%{_saltceph}/osd/partition/*.sls
%config /%{_saltceph}/osd/scheduler/*.sls
%config /%{_saltceph}/packages/*.sls
%config /%{_saltceph}/packages/common/*.sls
%config /%{_saltceph}/pool/*.sls
%config /%{_saltceph}/reactor/*.sls
%config /%{_saltceph}/refresh/*.sls
%config /%{_saltceph}/repo/*.sls
%config /%{_saltceph}/remove/igw/auth/*.sls
%config /%{_saltceph}/remove/mon/*.sls
%config /%{_saltceph}/remove/mds/*.sls
%config /%{_saltceph}/remove/rgw/*.sls
%config /%{_saltceph}/remove/storage/*.sls
%config /%{_saltceph}/rescind/*.sls
%config /%{_saltceph}/rescind/admin/*.sls
%config /%{_saltceph}/rescind/igw-client/*.sls
%config /%{_saltceph}/rescind/igw/*.sls
%config /%{_saltceph}/rescind/igw/keyring/*.sls
%config /%{_saltceph}/rescind/igw/lrbd/*.sls
%config /%{_saltceph}/rescind/igw/sysconfig/*.sls
%config /%{_saltceph}/rescind/master/*.sls
%config /%{_saltceph}/rescind/mds-client/*.sls
%config /%{_saltceph}/rescind/mds-nfs/*.sls
%config /%{_saltceph}/rescind/mds/*.sls
%config /%{_saltceph}/rescind/mds/keyring/*.sls
%config /%{_saltceph}/rescind/mon/*.sls
%config /%{_saltceph}/rescind/rgw-client/*.sls
%config /%{_saltceph}/rescind/rgw-nfs/*.sls
%config /%{_saltceph}/rescind/rgw/*.sls
%config /%{_saltceph}/rescind/rgw/keyring/*.sls
%config /%{_saltceph}/rescind/storage/*.sls
%config /%{_saltceph}/rescind/storage/keyring/*.sls
%config /%{_saltceph}/rgw/*.sls
%config /%{_saltceph}/rgw/files/*.j2
%config /%{_saltceph}/rgw/key/*.sls
%config /%{_saltceph}/rgw/auth/*.sls
%config /%{_saltceph}/rgw/keyring/*.sls
%config /%{_saltceph}/stage/0
%config /%{_saltceph}/stage/1
%config /%{_saltceph}/stage/2
%config /%{_saltceph}/stage/3
%config /%{_saltceph}/stage/4
%config /%{_saltceph}/stage/5
%config /%{_saltceph}/stage/all/*.sls
%config /%{_saltceph}/stage/benchmark/*.sls
%config /%{_saltceph}/stage/cephfs/*.sls
%config /%{_saltceph}/stage/configure/*.sls
%config /%{_saltceph}/stage/deploy/*.sls
%config /%{_saltceph}/stage/discovery/*.sls
%config /%{_saltceph}/stage/iscsi/*.sls
%config /%{_saltceph}/stage/openattic/*.sls
%config /%{_saltceph}/stage/prep/*.sls
%config /%{_saltceph}/stage/prep/master/*.sls
%config /%{_saltceph}/stage/prep/minion/*.sls
%config /%{_saltceph}/stage/radosgw/*.sls
%config /%{_saltceph}/stage/removal/*.sls
%config /%{_saltceph}/stage/services/*.sls
%config /%{_saltceph}/sync/*.sls
%config /%{_saltceph}/time/*.sls
%config /%{_saltceph}/time/ntp/*.sls
%config /%{_saltceph}/updates/*.sls
%config /%{_saltceph}/updates/restart/*.sls
%doc
%dir %attr(-, root, root) %{_docdir}/%{name}
%{_docdir}/%{name}/*


%changelog
* Thu Sep  8 2016 Eric Jackson
- 
