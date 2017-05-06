# Override this to install docs somewhere else
DOCDIR = /usr/share/doc/packages

usage:
	@echo "Usage:"
	@echo -e "\tmake install\tInstall DeepSea on this host"
	@echo -e "\tmake rpm\tBuild an RPM for installation elsewhere"
	@echo -e "\tmake test\tRun unittests"

copy-files:
	# salt-master config files
	install -d -m 755 $(DESTDIR)/etc/salt/master.d
	install -m 644 etc/salt/master.d/modules.conf $(DESTDIR)/etc/salt/master.d/
	install -m 644 etc/salt/master.d/reactor.conf $(DESTDIR)/etc/salt/master.d/
	install -m 644 etc/salt/master.d/output.conf $(DESTDIR)/etc/salt/master.d/
	# docs
	install -d -m 755 $(DESTDIR)$(DOCDIR)/deepsea
	install -m 644 LICENSE $(DESTDIR)$(DOCDIR)/deepsea/
	install -m 644 README.md $(DESTDIR)$(DOCDIR)/deepsea/
	# examples
	install -d -m 755 $(DESTDIR)$(DOCDIR)/deepsea/examples
	install -m 644 doc/examples/* $(DESTDIR)$(DOCDIR)/deepsea/examples/
	# stacky.py (included in salt 2016.3)
	install -d -m 755 $(DESTDIR)/srv/modules/pillar
	install -m 644 srv/modules/pillar/stack.py $(DESTDIR)/srv/modules/pillar/
	# runners
	install -d -m 755 $(DESTDIR)/srv/modules/runners
	install -m 644 srv/modules/runners/*.py $(DESTDIR)/srv/modules/runners/
	# pillar
	install -d -m 755 $(DESTDIR)/srv/pillar/ceph
	install -d -m 755 $(DESTDIR)/srv/pillar/ceph/benchmark
	install -m 644 srv/pillar/ceph/benchmark/config.yml $(DESTDIR)/srv/pillar/ceph/benchmark/config.yml
	install -m 644 srv/pillar/ceph/benchmark/benchmark.cfg $(DESTDIR)/srv/pillar/ceph/benchmark/benchmark.cfg
	install -m 644 srv/pillar/ceph/benchmark/benchmark.cfg $(DESTDIR)/srv/pillar/ceph/benchmark/benchmark.cfg
	install -d -m 755 $(DESTDIR)/srv/pillar/ceph/benchmark/collections
	install -m 644 srv/pillar/ceph/benchmark/collections/*.yml $(DESTDIR)/srv/pillar/ceph/benchmark/collections
	install -d -m 755 $(DESTDIR)/srv/pillar/ceph/benchmark/fio
	install -m 644 srv/pillar/ceph/benchmark/fio/*.yml $(DESTDIR)/srv/pillar/ceph/benchmark/fio/
	install -d -m 755 $(DESTDIR)/srv/pillar/ceph/benchmark/templates
	install -m 644 srv/pillar/ceph/benchmark/templates/*.j2 $(DESTDIR)/srv/pillar/ceph/benchmark/templates/
	install -m 644 srv/pillar/ceph/init.sls $(DESTDIR)/srv/pillar/ceph/
	install -m 644 srv/pillar/ceph/master_minion.sls $(DESTDIR)/srv/pillar/ceph/
	install -d -m 755 $(DESTDIR)/srv/pillar/ceph/stack
	install -m 644 srv/pillar/ceph/stack/stack.cfg $(DESTDIR)/srv/pillar/ceph/stack/stack.cfg
	install -m 644 srv/pillar/top.sls $(DESTDIR)/srv/pillar/
	# modules
	install -d -m 755 $(DESTDIR)/srv/salt/_modules
	install -m 644 srv/salt/_modules/*.py $(DESTDIR)/srv/salt/_modules/
	# state files
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/admin
	install -m 644 srv/salt/ceph/admin/*.sls $(DESTDIR)/srv/salt/ceph/admin/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/admin/key
	install -m 644 srv/salt/ceph/admin/key/*.sls $(DESTDIR)/srv/salt/ceph/admin/key/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/admin/files
	install -m 644 srv/salt/ceph/admin/files/*.j2 $(DESTDIR)/srv/salt/ceph/admin/files/
	# state files benchmarks
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/benchmarks
	install -m 644 srv/salt/ceph/benchmarks/*.sls $(DESTDIR)/srv/salt/ceph/benchmarks/
	# state files cephfs
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/cephfs
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/cephfs/benchmarks
	install -m 644 srv/salt/ceph/cephfs/benchmarks/*.sls $(DESTDIR)/srv/salt/ceph/cephfs/benchmarks/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/cephfs/benchmarks/files
	install -m 644 srv/salt/ceph/cephfs/benchmarks/files/fio.service $(DESTDIR)/srv/salt/ceph/cephfs/benchmarks/files
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/configuration
	install -m 644 srv/salt/ceph/configuration/*.sls $(DESTDIR)/srv/salt/ceph/configuration/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/configuration/check
	install -m 644 srv/salt/ceph/configuration/check/*.sls $(DESTDIR)/srv/salt/ceph/configuration/check/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/configuration/files
	install -m 644 srv/salt/ceph/configuration/files/ceph.conf* $(DESTDIR)/srv/salt/ceph/configuration/files/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/events
	install -m 644 srv/salt/ceph/events/*.sls $(DESTDIR)/srv/salt/ceph/events/
	# state files - diagnose
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/diagnose
	install -m 644 srv/salt/ceph/diagnose/*.md $(DESTDIR)/srv/salt/ceph/diagnose
	install -m 644 srv/salt/ceph/diagnose/*.sls $(DESTDIR)/srv/salt/ceph/diagnose
	# state files - ganesha
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/ganesha
	install -m 644 srv/salt/ceph/ganesha/*.sls $(DESTDIR)/srv/salt/ceph/ganesha/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/ganesha/auth
	install -m 644 srv/salt/ceph/ganesha/auth/*.sls $(DESTDIR)/srv/salt/ceph/ganesha/auth
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/ganesha/files
	install -m 644 srv/salt/ceph/ganesha/files/*.j2 $(DESTDIR)/srv/salt/ceph/ganesha/files
	install -m 644 srv/salt/ceph/ganesha/files/ganesha.service $(DESTDIR)/srv/salt/ceph/ganesha/files
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/ganesha/config
	install -m 644 srv/salt/ceph/ganesha/config/*.sls $(DESTDIR)/srv/salt/ceph/ganesha/config/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/ganesha/configure
	install -m 644 srv/salt/ceph/ganesha/configure/*.sls $(DESTDIR)/srv/salt/ceph/ganesha/configure/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/ganesha/key
	install -m 644 srv/salt/ceph/ganesha/key/*.sls $(DESTDIR)/srv/salt/ceph/ganesha/key/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/ganesha/keyring
	install -m 644 srv/salt/ceph/ganesha/keyring/*.sls $(DESTDIR)/srv/salt/ceph/ganesha/keyring/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/ganesha/install
	install -m 644 srv/salt/ceph/ganesha/install/*.sls $(DESTDIR)/srv/salt/ceph/ganesha/install/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/ganesha/service
	install -m 644 srv/salt/ceph/ganesha/service/*.sls $(DESTDIR)/srv/salt/ceph/ganesha/service/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/ganesha/restart
	install -m 644 srv/salt/ceph/ganesha/service/*.sls $(DESTDIR)/srv/salt/ceph/ganesha/restart/
	# state files - igw
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/igw
	install -m 644 srv/salt/ceph/igw/*.sls $(DESTDIR)/srv/salt/ceph/igw/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/igw/files
	install -m 644 srv/salt/ceph/igw/files/*.j2 $(DESTDIR)/srv/salt/ceph/igw/files/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/igw/config
	install -m 644 srv/salt/ceph/igw/config/*.sls $(DESTDIR)/srv/salt/ceph/igw/config/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/igw/import
	install -m 644 srv/salt/ceph/igw/import/*.sls $(DESTDIR)/srv/salt/ceph/igw/import/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/igw/key
	install -m 644 srv/salt/ceph/igw/key/*.sls $(DESTDIR)/srv/salt/ceph/igw/key/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/igw/auth
	install -m 644 srv/salt/ceph/igw/auth/*.sls $(DESTDIR)/srv/salt/ceph/igw/auth/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/igw/keyring
	install -m 644 srv/salt/ceph/igw/keyring/*.sls $(DESTDIR)/srv/salt/ceph/igw/keyring/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/igw/sysconfig
	install -m 644 srv/salt/ceph/igw/sysconfig/*.sls $(DESTDIR)/srv/salt/ceph/igw/sysconfig/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/igw/restart
	install -m 644 srv/salt/ceph/igw/restart/*.sls $(DESTDIR)/srv/salt/ceph/igw/restart
	# state files - iperf
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/iperf
	install -m 644 srv/salt/ceph/iperf/*.sls $(DESTDIR)/srv/salt/ceph/iperf/
	install -m 644 srv/salt/ceph/iperf/systemd-iperf.service $(DESTDIR)/srv/salt/ceph/iperf/
	install -m 644 srv/salt/ceph/iperf/*.py $(DESTDIR)/srv/salt/ceph/iperf
	# state files - mds
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/mds
	install -m 644 srv/salt/ceph/mds/*.sls $(DESTDIR)/srv/salt/ceph/mds/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/mds/key
	install -m 644 srv/salt/ceph/mds/key/*.sls $(DESTDIR)/srv/salt/ceph/mds/key/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/mds/auth
	install -m 644 srv/salt/ceph/mds/auth/*.sls $(DESTDIR)/srv/salt/ceph/mds/auth/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/mds/keyring
	install -m 644 srv/salt/ceph/mds/keyring/*.sls $(DESTDIR)/srv/salt/ceph/mds/keyring/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/mds/pools
	install -m 644 srv/salt/ceph/mds/pools/*.sls $(DESTDIR)/srv/salt/ceph/mds/pools/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/mds/files
	install -m 644 srv/salt/ceph/mds/files/*.j2 $(DESTDIR)/srv/salt/ceph/mds/files/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/mds/restart
	install -m 644 srv/salt/ceph/mds/restart/*.sls $(DESTDIR)/srv/salt/ceph/mds/restart
	# state files - salt-api
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/cherrypy
	install -m 644 srv/salt/ceph/cherrypy/*.sls $(DESTDIR)/srv/salt/ceph/cherrypy
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/cherrypy/files
	install -m 644 srv/salt/ceph/cherrypy/files/*.conf* $(DESTDIR)/srv/salt/ceph/cherrypy/files

	# state files - mines
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/mines
	install -m 644 srv/salt/ceph/mines/*.sls $(DESTDIR)/srv/salt/ceph/mines/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/mines/files
	install -m 644 srv/salt/ceph/mines/files/* $(DESTDIR)/srv/salt/ceph/mines/files/
	# state files - mon
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/mon
	install -m 644 srv/salt/ceph/mon/*.sls $(DESTDIR)/srv/salt/ceph/mon/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/mon/key
	install -m 644 srv/salt/ceph/mon/key/*.sls $(DESTDIR)/srv/salt/ceph/mon/key/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/mon/files
	install -m 644 srv/salt/ceph/mon/files/*.j2 $(DESTDIR)/srv/salt/ceph/mon/files/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/mon/restart
	install -m 644 srv/salt/ceph/mon/restart/*.sls $(DESTDIR)/srv/salt/ceph/mon/restart
	# state files - noout
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/noout
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/noout/set
	install -m 644 srv/salt/ceph/noout/set/*.sls $(DESTDIR)/srv/salt/ceph/noout/set
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/noout/unset
	install -m 644 srv/salt/ceph/noout/unset/*.sls $(DESTDIR)/srv/salt/ceph/noout/unset
	# state files - openattic
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/openattic
	install -m 644 srv/salt/ceph/openattic/*.sls $(DESTDIR)/srv/salt/ceph/openattic/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/openattic/auth
	install -m 644 srv/salt/ceph/openattic/auth/*.sls $(DESTDIR)/srv/salt/ceph/openattic/auth/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/openattic/files
	install -m 644 srv/salt/ceph/openattic/files/*.j2 $(DESTDIR)/srv/salt/ceph/openattic/files/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/openattic/key
	install -m 644 srv/salt/ceph/openattic/key/*.sls $(DESTDIR)/srv/salt/ceph/openattic/key/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/openattic/keyring
	install -m 644 srv/salt/ceph/openattic/keyring/*.sls $(DESTDIR)/srv/salt/ceph/openattic/keyring/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/openattic/oaconfig
	install -m 644 srv/salt/ceph/openattic/oaconfig/*.sls $(DESTDIR)/srv/salt/ceph/openattic/oaconfig/
	# state files - osd
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/osd
	install -m 644 srv/salt/ceph/osd/*.sls $(DESTDIR)/srv/salt/ceph/osd/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/osd/key
	install -m 644 srv/salt/ceph/osd/key/*.sls $(DESTDIR)/srv/salt/ceph/osd/key/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/osd/auth
	install -m 644 srv/salt/ceph/osd/auth/*.sls $(DESTDIR)/srv/salt/ceph/osd/auth/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/osd/keyring
	install -m 644 srv/salt/ceph/osd/keyring/*.sls $(DESTDIR)/srv/salt/ceph/osd/keyring/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/osd/partition
	install -m 644 srv/salt/ceph/osd/partition/*.sls $(DESTDIR)/srv/salt/ceph/osd/partition/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/osd/scheduler
	install -m 644 srv/salt/ceph/osd/scheduler/*.sls $(DESTDIR)/srv/salt/ceph/osd/scheduler/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/osd/files
	install -m 644 srv/salt/ceph/osd/files/*.j2 $(DESTDIR)/srv/salt/ceph/osd/files/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/osd/restart
	install -m 644 srv/salt/ceph/osd/restart/default.sls $(DESTDIR)/srv/salt/ceph/osd/restart
	install -m 644 srv/salt/ceph/osd/restart/init.sls $(DESTDIR)/srv/salt/ceph/osd/restart
	# state files - packages
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/packages
	install -m 644 srv/salt/ceph/packages/*.sls $(DESTDIR)/srv/salt/ceph/packages/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/packages/common
	install -m 644 srv/salt/ceph/packages/common/*.sls $(DESTDIR)/srv/salt/ceph/packages/common/
	# state files - pool
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/pool
	install -m 644 srv/salt/ceph/pool/*.sls $(DESTDIR)/srv/salt/ceph/pool/
	# state files - purge
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/purge
	install -m 644 srv/salt/ceph/purge/*.sls $(DESTDIR)/srv/salt/ceph/purge/
	# state files - reactor
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/reactor
	install -m 644 srv/salt/ceph/reactor/*.sls $(DESTDIR)/srv/salt/ceph/reactor/
	# state files - refresh
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/refresh
	install -m 644 srv/salt/ceph/refresh/*.sls $(DESTDIR)/srv/salt/ceph/refresh/
	# state files - remove
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/remove
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/remove/igw/auth
	install -m 644 srv/salt/ceph/remove/igw/auth/*.sls $(DESTDIR)/srv/salt/ceph/remove/igw/auth/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/remove/mds
	install -m 644 srv/salt/ceph/remove/mds/*.sls $(DESTDIR)/srv/salt/ceph/remove/mds/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/remove/mon
	install -m 644 srv/salt/ceph/remove/mon/*.sls $(DESTDIR)/srv/salt/ceph/remove/mon/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/remove/rgw
	install -m 644 srv/salt/ceph/remove/rgw/*.sls $(DESTDIR)/srv/salt/ceph/remove/rgw/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/remove/ganesha
	install -m 644 srv/salt/ceph/remove/ganesha/*.sls $(DESTDIR)/srv/salt/ceph/remove/ganesha/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/remove/storage
	install -m 644 srv/salt/ceph/remove/storage/*.sls $(DESTDIR)/srv/salt/ceph/remove/storage/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/remove/openattic
	install -m 644 srv/salt/ceph/remove/openattic/*.sls $(DESTDIR)/srv/salt/ceph/remove/openattic/
	# state files - rescind
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/rescind
	install -m 644 srv/salt/ceph/rescind/*.sls $(DESTDIR)/srv/salt/ceph/rescind/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/rescind/admin
	install -m 644 srv/salt/ceph/rescind/admin/*.sls $(DESTDIR)/srv/salt/ceph/rescind/admin/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/rescind/client-iscsi
	install -m 644 srv/salt/ceph/rescind/client-iscsi/*.sls $(DESTDIR)/srv/salt/ceph/rescind/client-iscsi/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/rescind/ganesha
	install -m 644 srv/salt/ceph/rescind/ganesha/*.sls $(DESTDIR)/srv/salt/ceph/rescind/ganesha/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/rescind/igw
	install -m 644 srv/salt/ceph/rescind/igw/*.sls $(DESTDIR)/srv/salt/ceph/rescind/igw/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/rescind/igw/keyring
	install -m 644 srv/salt/ceph/rescind/igw/keyring/*.sls $(DESTDIR)/srv/salt/ceph/rescind/igw/keyring/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/rescind/igw/lrbd
	install -m 644 srv/salt/ceph/rescind/igw/lrbd/*.sls $(DESTDIR)/srv/salt/ceph/rescind/igw/lrbd/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/rescind/igw/sysconfig
	install -m 644 srv/salt/ceph/rescind/igw/sysconfig/*.sls $(DESTDIR)/srv/salt/ceph/rescind/igw/sysconfig/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/rescind/master
	install -m 644 srv/salt/ceph/rescind/master/*.sls $(DESTDIR)/srv/salt/ceph/rescind/master/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/rescind/client-cephfs
	install -m 644 srv/salt/ceph/rescind/client-cephfs/*.sls $(DESTDIR)/srv/salt/ceph/rescind/client-cephfs/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/rescind/client-nfs
	install -m 644 srv/salt/ceph/rescind/client-nfs/*.sls $(DESTDIR)/srv/salt/ceph/rescind/client-nfs/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/rescind/mds-nfs
	install -m 644 srv/salt/ceph/rescind/mds-nfs/*.sls $(DESTDIR)/srv/salt/ceph/rescind/mds-nfs/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/rescind/mds
	install -m 644 srv/salt/ceph/rescind/mds/*.sls $(DESTDIR)/srv/salt/ceph/rescind/mds/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/rescind/mds/keyring
	install -m 644 srv/salt/ceph/rescind/mds/keyring/*.sls $(DESTDIR)/srv/salt/ceph/rescind/mds/keyring/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/rescind/mon
	install -m 644 srv/salt/ceph/rescind/mon/*.sls $(DESTDIR)/srv/salt/ceph/rescind/mon/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/rescind/admin
	install -m 644 srv/salt/ceph/rescind/admin/*.sls $(DESTDIR)/srv/salt/ceph/rescind/admin/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/rescind/client-radosgw
	install -m 644 srv/salt/ceph/rescind/client-radosgw/*.sls $(DESTDIR)/srv/salt/ceph/rescind/client-radosgw/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/rescind/rgw-nfs
	install -m 644 srv/salt/ceph/rescind/rgw-nfs/*.sls $(DESTDIR)/srv/salt/ceph/rescind/rgw-nfs/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/rescind/rgw
	install -m 644 srv/salt/ceph/rescind/rgw/*.sls $(DESTDIR)/srv/salt/ceph/rescind/rgw/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/rescind/rgw/keyring
	install -m 644 srv/salt/ceph/rescind/rgw/keyring/*.sls $(DESTDIR)/srv/salt/ceph/rescind/rgw/keyring/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/rescind/storage
	install -m 644 srv/salt/ceph/rescind/storage/*.sls $(DESTDIR)/srv/salt/ceph/rescind/storage/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/rescind/storage/keyring
	install -m 644 srv/salt/ceph/rescind/storage/keyring/*.sls $(DESTDIR)/srv/salt/ceph/rescind/storage/keyring/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/rescind/openattic
	install -m 644 srv/salt/ceph/rescind/openattic/*.sls $(DESTDIR)/srv/salt/ceph/rescind/openattic/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/rescind/openattic/keyring
	install -m 644 srv/salt/ceph/rescind/openattic/keyring/*.sls $(DESTDIR)/srv/salt/ceph/rescind/openattic/keyring/
	# state files - repo
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/repo
	install -m 644 srv/salt/ceph/repo/*.sls $(DESTDIR)/srv/salt/ceph/repo/
	# state files - restart
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/restart
	install -m 644 srv/salt/ceph/restart/*.sls $(DESTDIR)/srv/salt/ceph/restart/
	# state files - reset
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/reset
	install -m 644 srv/salt/ceph/reset/*.sls $(DESTDIR)/srv/salt/ceph/reset/
	# state files - rgw
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/rgw
	install -m 644 srv/salt/ceph/rgw/*.sls $(DESTDIR)/srv/salt/ceph/rgw/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/rgw/key
	install -m 644 srv/salt/ceph/rgw/key/*.sls $(DESTDIR)/srv/salt/ceph/rgw/key/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/rgw/auth
	install -m 644 srv/salt/ceph/rgw/auth/*.sls $(DESTDIR)/srv/salt/ceph/rgw/auth/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/rgw/keyring
	install -m 644 srv/salt/ceph/rgw/keyring/*.sls $(DESTDIR)/srv/salt/ceph/rgw/keyring/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/rgw/users
	install -m 644 srv/salt/ceph/rgw/users/*.sls $(DESTDIR)/srv/salt/ceph/rgw/users/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/rgw/files
	install -m 644 srv/salt/ceph/rgw/files/*.j2 $(DESTDIR)/srv/salt/ceph/rgw/files/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/rgw/restart
	install -m 644 srv/salt/ceph/rgw/restart/default.sls $(DESTDIR)/srv/salt/ceph/rgw/restart
	install -m 644 srv/salt/ceph/rgw/restart/init.sls $(DESTDIR)/srv/salt/ceph/rgw/restart
	# state files - update
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/upgrade
	install -m 644 srv/salt/ceph/upgrade/*.sls $(DESTDIR)/srv/salt/ceph/upgrade
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/updates
	install -m 644 srv/salt/ceph/updates/*.sls $(DESTDIR)/srv/salt/ceph/updates/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/updates/restart
	install -m 644 srv/salt/ceph/updates/restart/*.sls $(DESTDIR)/srv/salt/ceph/updates/restart/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/updates/regular
	install -m 644 srv/salt/ceph/updates/regular/*.sls $(DESTDIR)/srv/salt/ceph/updates/regular/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/updates/kernel
	install -m 644 srv/salt/ceph/updates/kernel/*.sls $(DESTDIR)/srv/salt/ceph/updates/kernel/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/updates/master
	install -m 644 srv/salt/ceph/updates/master/*.sls $(DESTDIR)/srv/salt/ceph/updates/master/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/updates/salt
	install -m 644 srv/salt/ceph/updates/salt/*.sls $(DESTDIR)/srv/salt/ceph/updates/salt/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/maintenance
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/maintenance/upgrade
	install -m 644 srv/salt/ceph/maintenance/upgrade/*.sls $(DESTDIR)/srv/salt/ceph/maintenance/upgrade
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/maintenance/noout
	install -m 644 srv/salt/ceph/maintenance/noout/*.sls $(DESTDIR)/srv/salt/ceph/maintenance/noout
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/maintenance/upgrade/master
	install -m 644 srv/salt/ceph/maintenance/upgrade/master/*.sls $(DESTDIR)/srv/salt/ceph/maintenance/upgrade/master
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/maintenance/upgrade/minion
	install -m 644 srv/salt/ceph/maintenance/upgrade/minion/*.sls $(DESTDIR)/srv/salt/ceph/maintenance/upgrade/minion
	# state files - orchestrate stages
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/stage/all
	install -m 644 srv/salt/ceph/stage/all/*.sls $(DESTDIR)/srv/salt/ceph/stage/all/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/stage/benchmark
	install -m 644 srv/salt/ceph/stage/benchmark/*.sls $(DESTDIR)/srv/salt/ceph/stage/benchmark/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/stage/cephfs
	install -m 644 srv/salt/ceph/stage/cephfs/*.sls $(DESTDIR)/srv/salt/ceph/stage/cephfs/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/stage/configure
	install -m 644 srv/salt/ceph/stage/configure/*.sls $(DESTDIR)/srv/salt/ceph/stage/configure/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/stage/deploy
	install -m 644 srv/salt/ceph/stage/deploy/*.sls $(DESTDIR)/srv/salt/ceph/stage/deploy/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/stage/discovery
	install -m 644 srv/salt/ceph/stage/discovery/*.sls $(DESTDIR)/srv/salt/ceph/stage/discovery/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/stage/ganesha
	install -m 644 srv/salt/ceph/stage/ganesha/*.sls $(DESTDIR)/srv/salt/ceph/stage/ganesha/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/stage/iscsi
	install -m 644 srv/salt/ceph/stage/iscsi/*.sls $(DESTDIR)/srv/salt/ceph/stage/iscsi/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/stage/openattic
	install -m 644 srv/salt/ceph/stage/openattic/*.sls $(DESTDIR)/srv/salt/ceph/stage/openattic/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/stage/prep
	install -m 644 srv/salt/ceph/stage/prep/*.sls $(DESTDIR)/srv/salt/ceph/stage/prep/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/stage/prep/master
	install -m 644 srv/salt/ceph/stage/prep/master/*.sls $(DESTDIR)/srv/salt/ceph/stage/prep/master/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/stage/prep/minion
	install -m 644 srv/salt/ceph/stage/prep/minion/*.sls $(DESTDIR)/srv/salt/ceph/stage/prep/minion/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/stage/removal
	install -m 644 srv/salt/ceph/stage/removal/*.sls $(DESTDIR)/srv/salt/ceph/stage/removal/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/stage/radosgw
	install -m 644 srv/salt/ceph/stage/radosgw/*.sls $(DESTDIR)/srv/salt/ceph/stage/radosgw/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/stage/services
	install -m 644 srv/salt/ceph/stage/services/*.sls $(DESTDIR)/srv/salt/ceph/stage/services/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/sync
	install -m 644 srv/salt/ceph/sync/*.sls $(DESTDIR)/srv/salt/ceph/sync/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/time
	install -m 644 srv/salt/ceph/time/default.sls $(DESTDIR)/srv/salt/ceph/time/
	install -m 644 srv/salt/ceph/time/init.sls $(DESTDIR)/srv/salt/ceph/time/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/time/ntp
	install -m 644 srv/salt/ceph/time/ntp/*.sls $(DESTDIR)/srv/salt/ceph/time/ntp/
	# state files - wait
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/wait
	install -m 644 srv/salt/ceph/wait/*.sls $(DESTDIR)/srv/salt/ceph/wait/
	# state files - check processes
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/processes
	install -m 644 srv/salt/ceph/processes/*.sls $(DESTDIR)/srv/salt/ceph/processes/
	# state files - warning
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/warning
	install -m 644 srv/salt/ceph/warning/*.sls $(DESTDIR)/srv/salt/ceph/warning/
	# state files - warning/noout
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/warning/noout
	install -m 644 srv/salt/ceph/warning/noout/*.sls $(DESTDIR)/srv/salt/ceph/warning/noout/

	# state files - orchestrate stage symlinks
	ln -sf prep		$(DESTDIR)/srv/salt/ceph/stage/0
	ln -sf discovery	$(DESTDIR)/srv/salt/ceph/stage/1
	ln -sf configure	$(DESTDIR)/srv/salt/ceph/stage/2
	ln -sf deploy		$(DESTDIR)/srv/salt/ceph/stage/3
	ln -sf services		$(DESTDIR)/srv/salt/ceph/stage/4
	ln -sf removal		$(DESTDIR)/srv/salt/ceph/stage/5

install: copy-files
	sed -i '/^master_minion:/s!_REPLACE_ME_!'`hostname -f`'!' /srv/pillar/ceph/master_minion.sls
	chown -R salt /srv/pillar/ceph
	systemctl restart salt-master

rpm: tarball test
	rpmbuild -bb deepsea.spec

# Removing test dependency until resolved
tarball:
	VERSION=`awk '/^Version/ {print $$2}' deepsea.spec`; \
	git archive --prefix deepsea-$$VERSION/ -o ~/rpmbuild/SOURCES/deepsea-$$VERSION.tar.gz HEAD

test:
	tox -e py27
