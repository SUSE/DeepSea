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
Version:        0.4.1
Release:        0
Summary:        Salt solution for deploying and managing Ceph

License:        GPL-3.0
Group:          System/Libraries
Url:            http://bugs.opensuse.org
Source0:        deepsea-%{version}.tar.gz

Requires:       salt
BuildRoot:      %{_tmppath}/%{name}-%{version}-build
BuildArch:      noarch

%description
A collection of Salt files providing a deployment of Ceph as a series of stages.


%prep

%build
%__tar xvzf %{SOURCE0}

%install
install -d 755 %{buildroot}%{_mandir}/man8

cd %{name}

install -d 755 %{buildroot}/etc/salt/master.d
install -m 644 etc/salt/master.d/modules.conf %{buildroot}/etc/salt/master.d/
install -m 644 etc/salt/master.d/reactor.conf %{buildroot}/etc/salt/master.d/

install -d 755 %{buildroot}%{_docdir}/%{name}
install -m 644 LICENSE %{buildroot}%{_docdir}/%{name}
install -m 644 README.md %{buildroot}%{_docdir}/%{name}

install -d 755 %{buildroot}%{_docdir}/%{name}/examples
install -m 644 doc/examples/policy.cfg-rolebased %{buildroot}%{_docdir}/%{name}/examples
install -m 644 doc/examples/policy.cfg-generic %{buildroot}%{_docdir}/%{name}/examples
install -m 644 doc/examples/policy.cfg-regex %{buildroot}%{_docdir}/%{name}/examples

# Included in Salt 2016.3
install -d 755 %{buildroot}/srv/modules/pillar
install -m 644 srv/modules/pillar/stack.py %{buildroot}/srv/modules/pillar

%define _runners srv/modules/runners
install -d 755 %{buildroot}/%{_runners}
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
install -d 755 %{buildroot}/%{_pillar}/ceph
install -m 644 %{_pillar}/ceph/cluster/README %{buildroot}/%{_pillar}/ceph
install -m 644 %{_pillar}/ceph/init.sls %{buildroot}/%{_pillar}/ceph
install -m 644 %{_pillar}/ceph/master_minion.sls %{buildroot}/%{_pillar}/ceph

install -d 755 %{buildroot}/%{_pillar}/ceph/stack
install -m 644 %{_pillar}/ceph/stack/stack.cfg %{buildroot}/%{_pillar}/ceph/stack/stack.cfg

install -m 644 %{_pillar}/top.sls %{buildroot}/%{_pillar}

install -d 755 %{buildroot}/srv/salt/_modules
install -m 644 srv/salt/_modules/cephdisks.py %{buildroot}/srv/salt/_modules
install -m 644 srv/salt/_modules/freedisks.py %{buildroot}/srv/salt/_modules
install -m 644 srv/salt/_modules/retry.py %{buildroot}/srv/salt/_modules
install -m 644 srv/salt/_modules/wait.py %{buildroot}/srv/salt/_modules
install -m 644 srv/salt/_modules/zypper_locks.py %{buildroot}/srv/salt/_modules

%define _saltceph srv/salt/ceph
install -d 755 %{buildroot}/%{_saltceph}/admin
install -m 644 %{_saltceph}/admin/authtool.sls %{buildroot}/%{_saltceph}/admin
install -m 644 %{_saltceph}/admin/default.sls %{buildroot}/%{_saltceph}/admin
install -d 755 %{buildroot}/%{_saltceph}/admin/files
install -m 644 %{_saltceph}/admin/files/keyring.j2 %{buildroot}/%{_saltceph}/admin/files
install -m 644 %{_saltceph}/admin/init.sls %{buildroot}/%{_saltceph}/admin
install -m 644 %{_saltceph}/admin/pcc.sls %{buildroot}/%{_saltceph}/admin

install -d 755 %{buildroot}/%{_saltceph}/configuration
install -m 644 %{_saltceph}/configuration/default.sls %{buildroot}/%{_saltceph}/configuration
install -m 644 %{_saltceph}/configuration/init.sls %{buildroot}/%{_saltceph}/configuration
install -d 755 %{buildroot}/%{_saltceph}/configuration/files
install -m 644 %{_saltceph}/configuration/files/ceph.conf.j2 %{buildroot}/%{_saltceph}/configuration/files


install -d 755 %{buildroot}/%{_saltceph}/events
install -m 644 %{_saltceph}/events/begin_prep.sls %{buildroot}/%{_saltceph}/events
install -m 644 %{_saltceph}/events/complete_prep.sls %{buildroot}/%{_saltceph}/events

#install -m 644 %{_saltceph}/files/multipath.conf
#install -m 644 %{_saltceph}/initiator/iscsiadm-salt.sls
#install -m 644 %{_saltceph}/initiator/iscsiadm.sls
#install -m 644 %{_saltceph}/initiator/multipathd.sls

install -d 755 %{buildroot}/%{_saltceph}/iscsi
install -m 644 %{_saltceph}/iscsi/authtool.sls %{buildroot}/%{_saltceph}/iscsi

install -m 644 %{_saltceph}/iscsi/files/sysconfig.lrbd %{buildroot}/%{_saltceph}/iscsi
install -d 755 %{buildroot}/%{_saltceph}/iscsi/files
install -m 644 %{_saltceph}/iscsi/files/keyring.j2 %{buildroot}/%{_saltceph}/iscsi/files
install -m 644 %{_saltceph}/iscsi/import-salt.sls %{buildroot}/%{_saltceph}/iscsi
install -m 644 %{_saltceph}/iscsi/import.sls %{buildroot}/%{_saltceph}/iscsi
install -m 644 %{_saltceph}/iscsi/keyring.sls %{buildroot}/%{_saltceph}/iscsi
install -m 644 %{_saltceph}/iscsi/lrbd-salt.sls %{buildroot}/%{_saltceph}/iscsi
install -m 644 %{_saltceph}/iscsi/lrbd.sls %{buildroot}/%{_saltceph}/iscsi
install -m 644 %{_saltceph}/iscsi/sysconfig.sls %{buildroot}/%{_saltceph}/iscsi


install -d 755 %{buildroot}/%{_saltceph}/mds
install -m 644 %{_saltceph}/mds/auth.sls %{buildroot}/%{_saltceph}/mds
install -m 644 %{_saltceph}/mds/bootstrap-auth.sls %{buildroot}/%{_saltceph}/mds
install -m 644 %{_saltceph}/mds/default.sls %{buildroot}/%{_saltceph}/mds

install -d 755 %{buildroot}/%{_saltceph}/mds/files
install -m 644 %{_saltceph}/mds/files/bootstrap.j2 %{buildroot}/%{_saltceph}/mds/files
install -m 644 %{_saltceph}/mds/files/keyring.j2 %{buildroot}/%{_saltceph}/mds/files
install -m 644 %{_saltceph}/mds/init.sls %{buildroot}/%{_saltceph}/mds
install -m 644 %{_saltceph}/mds/keyring.sls %{buildroot}/%{_saltceph}/mds
install -m 644 %{_saltceph}/mds/pcc.sls %{buildroot}/%{_saltceph}/mds
install -m 644 %{_saltceph}/mds/pools.sls %{buildroot}/%{_saltceph}/mds


install -d 755 %{buildroot}/%{_saltceph}/mine_functions
install -m 644 %{_saltceph}/mine_functions/init.sls %{buildroot}/%{_saltceph}/mine_functions
install -d 755 %{buildroot}/%{_saltceph}/mine_functions/files
install -m 644 %{_saltceph}/mine_functions/files/mine_functions.conf %{buildroot}/%{_saltceph}/mine_functions/files

install -d 755 %{buildroot}/%{_saltceph}/mon
install -m 644 %{_saltceph}/mon/default.sls %{buildroot}/%{_saltceph}/mon

install -d 755 %{buildroot}/%{_saltceph}/mon/files
install -m 644 %{_saltceph}/mon/files/keyring.j2 %{buildroot}/%{_saltceph}/mon/files
install -m 644 %{_saltceph}/mon/init.sls %{buildroot}/%{_saltceph}/mon
install -m 644 %{_saltceph}/mon/pcc.sls %{buildroot}/%{_saltceph}/mon
install -m 644 %{_saltceph}/mon/start.sls %{buildroot}/%{_saltceph}/mon

install -d 755 %{buildroot}/%{_saltceph}/openattic
install -m 644 %{_saltceph}/openattic/authtool.sls %{buildroot}/%{_saltceph}/openattic
install -m 644 %{_saltceph}/openattic/files/ceph.client.openattic.keyring %{buildroot}/%{_saltceph}/openattic
install -m 644 %{_saltceph}/openattic/init.sls %{buildroot}/%{_saltceph}/openattic
install -m 644 %{_saltceph}/openattic/keyring.sls %{buildroot}/%{_saltceph}/openattic
install -m 644 %{_saltceph}/openattic/openattic.sls %{buildroot}/%{_saltceph}/openattic

install -d 755 %{buildroot}/%{_saltceph}/osd
install -m 644 %{_saltceph}/osd/auth.sls %{buildroot}/%{_saltceph}/osd
install -m 644 %{_saltceph}/osd/custom.sls %{buildroot}/%{_saltceph}/osd
install -m 644 %{_saltceph}/osd/default.sls %{buildroot}/%{_saltceph}/osd

install -d 755 %{buildroot}/%{_saltceph}/osd/files
install -m 644 %{_saltceph}/osd/files/keyring.j2 %{buildroot}/%{_saltceph}/osd/files
install -m 644 %{_saltceph}/osd/init.sls %{buildroot}/%{_saltceph}/osd
install -m 644 %{_saltceph}/osd/keyring.sls %{buildroot}/%{_saltceph}/osd
install -m 644 %{_saltceph}/osd/partition.sls %{buildroot}/%{_saltceph}/osd
install -m 644 %{_saltceph}/osd/pcc-auth.sls %{buildroot}/%{_saltceph}/osd
install -m 644 %{_saltceph}/osd/pcc-custom.sls %{buildroot}/%{_saltceph}/osd
install -m 644 %{_saltceph}/osd/pcc-keyring.sls %{buildroot}/%{_saltceph}/osd
install -m 644 %{_saltceph}/osd/pcc.sls %{buildroot}/%{_saltceph}/osd
install -m 644 %{_saltceph}/osd/scheduler.sls %{buildroot}/%{_saltceph}/osd

install -d 755 %{buildroot}/%{_saltceph}/packages
install -m 644 %{_saltceph}/packages/custom-salt.sls %{buildroot}/%{_saltceph}/packages
install -m 644 %{_saltceph}/packages/default.sls %{buildroot}/%{_saltceph}/packages
install -m 644 %{_saltceph}/packages/init.sls %{buildroot}/%{_saltceph}/packages

install -d 755 %{buildroot}/%{_saltceph}/pool
install -m 644 %{_saltceph}/pool/custom.sls %{buildroot}/%{_saltceph}/pool
install -m 644 %{_saltceph}/pool/default.sls %{buildroot}/%{_saltceph}/pool
install -m 644 %{_saltceph}/pool/init.sls %{buildroot}/%{_saltceph}/pool

install -d 755 %{buildroot}/%{_saltceph}/reactor
install -m 644 %{_saltceph}/reactor/all_stages.sls %{buildroot}/%{_saltceph}/reactor
install -m 644 %{_saltceph}/reactor/discovery.sls %{buildroot}/%{_saltceph}/reactor
install -m 644 %{_saltceph}/reactor/highstate.sls %{buildroot}/%{_saltceph}/reactor
install -m 644 %{_saltceph}/reactor/initialize.sls %{buildroot}/%{_saltceph}/reactor
install -m 644 %{_saltceph}/reactor/master.sls %{buildroot}/%{_saltceph}/reactor
install -m 644 %{_saltceph}/reactor/prep_begin.sls %{buildroot}/%{_saltceph}/reactor
install -m 644 %{_saltceph}/reactor/prep_complete.sls %{buildroot}/%{_saltceph}/reactor
install -m 644 %{_saltceph}/reactor/prep_minion.sls %{buildroot}/%{_saltceph}/reactor
install -m 644 %{_saltceph}/reactor/readycheck %{buildroot}/%{_saltceph}/reactor

install -d 755 %{buildroot}/%{_saltceph}/refresh
install -m 644 %{_saltceph}/refresh/init.sls %{buildroot}/%{_saltceph}/refresh

install -d 755 %{buildroot}/%{_saltceph}/repo
install -m 644 %{_saltceph}/repo/custom.sls %{buildroot}/%{_saltceph}/repo
install -m 644 %{_saltceph}/repo/default.sls %{buildroot}/%{_saltceph}/repo
install -m 644 %{_saltceph}/repo/init.sls %{buildroot}/%{_saltceph}/repo

install -d 755 %{buildroot}/%{_saltceph}/rgw
install -m 644 %{_saltceph}/rgw/default.sls %{buildroot}/%{_saltceph}/rgw
install -m 644 %{_saltceph}/rgw/init.sls %{buildroot}/%{_saltceph}/rgw
install -m 644 %{_saltceph}/rgw/pools.sls %{buildroot}/%{_saltceph}/rgw

install -d 755 %{buildroot}/%{_saltceph}/stage
install -m 644 %{_saltceph}/stage/all.sls %{buildroot}/%{_saltceph}/stage
install -m 644 %{_saltceph}/stage/benchmark.sls %{buildroot}/%{_saltceph}/stage
install -m 644 %{_saltceph}/stage/cephfs.sls %{buildroot}/%{_saltceph}/stage
install -m 644 %{_saltceph}/stage/configure.sls %{buildroot}/%{_saltceph}/stage

install -d 755 %{buildroot}/%{_saltceph}/stage/configure
install -m 644 %{_saltceph}/stage/configure/default.sls %{buildroot}/%{_saltceph}/stage/configure
install -m 644 %{_saltceph}/stage/deploy.sls %{buildroot}/%{_saltceph}/stage
install -m 644 %{_saltceph}/stage/discovery.sls %{buildroot}/%{_saltceph}/stage

install -d 755 %{buildroot}/%{_saltceph}/stage/discovery
install -m 644 %{_saltceph}/stage/discovery/custom.sls %{buildroot}/%{_saltceph}/stage/discovery
install -m 644 %{_saltceph}/stage/discovery/default.sls %{buildroot}/%{_saltceph}/stage/discovery
install -m 644 %{_saltceph}/stage/iscsi.sls %{buildroot}/%{_saltceph}/stage
install -m 644 %{_saltceph}/stage/prep.sls %{buildroot}/%{_saltceph}/stage

install -d 755 %{buildroot}/%{_saltceph}/stage/prep
install -m 644 %{_saltceph}/stage/prep/default.sls %{buildroot}/%{_saltceph}/stage/prep
install -m 644 %{_saltceph}/stage/prep_minions.sls %{buildroot}/%{_saltceph}/stage
install -m 644 %{_saltceph}/stage/removal.sls %{buildroot}/%{_saltceph}/stage
install -m 644 %{_saltceph}/stage/rgw.sls %{buildroot}/%{_saltceph}/stage
install -m 644 %{_saltceph}/stage/services.sls %{buildroot}/%{_saltceph}/stage

install -d 755 %{buildroot}/%{_saltceph}/sync
install -m 644 %{_saltceph}/sync/init.sls %{buildroot}/%{_saltceph}/sync

install -d 755 %{buildroot}/%{_saltceph}/time
install -m 644 %{_saltceph}/time/custom-salt.sls %{buildroot}/%{_saltceph}/time
install -m 644 %{_saltceph}/time/custom.sls %{buildroot}/%{_saltceph}/time
install -m 644 %{_saltceph}/time/init.sls %{buildroot}/%{_saltceph}/time
install -m 644 %{_saltceph}/time/ntp.sls %{buildroot}/%{_saltceph}/time

install -d 755 %{buildroot}/%{_saltceph}/updates
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

%postun 

%files
%defattr(-,root,root,-)
/srv/modules/pillar/stack.py
%dir %attr(0750, root, salt) %_sysconfdir/salt
%dir %attr(0755, root, salt) /srv/salt
%dir %attr(0755, root, salt) /srv/pillar
%dir %attr(0755, root, salt) %{_sysconfdir}/salt/master.d/
%dir /%{_runners}
%dir /%{_pillar}
%dir /%{_pillar}/ceph
%dir /%{_pillar}/ceph/stack
%dir /srv/modules
%dir /srv/modules/pillar
%dir /srv/salt/_modules
%dir /%{_saltceph}
%dir /%{_saltceph}/admin
%dir /%{_saltceph}/admin/files
%dir /%{_saltceph}/configuration
%dir /%{_saltceph}/configuration/files
%dir /%{_saltceph}/events
%dir /%{_saltceph}/iscsi
%dir /%{_saltceph}/iscsi/files
%dir /%{_saltceph}/mds
%dir /%{_saltceph}/mds/files
%dir /%{_saltceph}/mine_functions
%dir /%{_saltceph}/mine_functions/files
%dir /%{_saltceph}/mon
%dir /%{_saltceph}/mon/files
%dir /%{_saltceph}/openattic
%dir /%{_saltceph}/osd
%dir /%{_saltceph}/osd/files
%dir /%{_saltceph}/packages
%dir /%{_saltceph}/pool
%dir /%{_saltceph}/reactor
%dir /%{_saltceph}/refresh
%dir /%{_saltceph}/repo
%dir /%{_saltceph}/rgw
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
%config /%{_saltceph}/configuration/*.sls
%config /%{_saltceph}/configuration/files/*.j2
%config /%{_saltceph}/events/*.sls
%config /%{_saltceph}/iscsi/*.sls
%config /%{_saltceph}/iscsi/sysconfig.lrbd
%config /%{_saltceph}/iscsi/files/*.j2
%config /%{_saltceph}/mds/*.sls
%config /%{_saltceph}/mds/files/*.j2
%config /%{_saltceph}/mine_functions/*.sls
%config /%{_saltceph}/mine_functions/files/*.conf
%config /%{_saltceph}/mon/*.sls
%config /%{_saltceph}/mon/files/*.j2
%config /%{_saltceph}/openattic/*.sls
%config /%{_saltceph}/openattic/ceph.client.openattic.keyring
%config /%{_saltceph}/osd/*.sls
%config /%{_saltceph}/osd/files/*.j2
%config /%{_saltceph}/packages/*.sls
%config /%{_saltceph}/pool/*.sls
%config /%{_saltceph}/reactor/*.sls
%config /%{_saltceph}/reactor/readycheck
%config /%{_saltceph}/refresh/*.sls
%config /%{_saltceph}/repo/*.sls
%config /%{_saltceph}/rgw/*.sls
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
