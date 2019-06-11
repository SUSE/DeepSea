# Override this to install docs somewhere else
DOCDIR = /usr/share/doc/packages
VERSION ?= $(shell (git describe --tags --long --match 'v*' 2>/dev/null || echo '0.0.0') | sed -e 's/^v//' -e 's/-/+/' -e 's/-/./')

DEEPSEA_DEPS=salt-api
PYTHON_DEPS=python3-setuptools python3-click python3-tox python3-configobj
PYTHON=python3

OS=$(shell source /etc/os-release 2>/dev/null ; echo $$ID)
suse=
ifneq (,$(findstring opensuse,$(OS)))
suse=yes
endif
ifeq ($(OS), sles)
suse=yes
endif
ifeq ($(suse), yes)
USER=salt
GROUP=salt
PKG_INSTALL=zypper -n install
else
USER=root
GROUP=root
ifeq ($(OS), centos)
PKG_INSTALL=yum install -y
PYTHON_DEPS=python-setuptools python-click python-tox python-configobj
PYTHON=python
else
ifeq ($(OS), fedora)
PKG_INSTALL=yum install -y
else
debian := $(wildcard /etc/debian_version)
ifneq ($(strip $(debian)),)
PKG_INSTALL=apt-get install -y
endif
endif
endif
endif


usage:
	@echo "Usage:"
	@echo -e "\tmake install\tInstall DeepSea on this host"
	@echo -e "\tmake rpm\tBuild an RPM for installation elsewhere"
	@echo -e "\tmake test\tRun unittests"

version:
	@echo "version: "$(VERSION)

setup.py:
	sed "s/DEVVERSION/"$(VERSION)"/" setup.py.in > setup.py

pyc: setup.py
	#make sure to create bytecode with the correct version
	find srv/ -name '*.py' -exec $(PYTHON) -m py_compile {} \;
	find cli/ -name '*.py' -exec $(PYTHON) -m py_compile {} \;

copy-files:
	# salt-master config files
	install -d -m 755 $(DESTDIR)/etc/salt/master.d
	install -m 644 etc/salt/master.d/modules.conf $(DESTDIR)/etc/salt/master.d/
	install -m 644 etc/salt/master.d/reactor.conf $(DESTDIR)/etc/salt/master.d/
	install -m 644 etc/salt/master.d/output.conf $(DESTDIR)/etc/salt/master.d/
	install -m 600 etc/salt/master.d/eauth.conf $(DESTDIR)/etc/salt/master.d/
	install -m 644 etc/salt/master.d/salt-api.conf $(DESTDIR)/etc/salt/master.d/
	install -m 600 srv/salt/ceph/salt-api/files/sharedsecret.conf.j2 $(DESTDIR)/etc/salt/master.d/sharedsecret.conf
	# tests
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/tests/keyrings
	install -m 644 srv/salt/ceph/tests/keyrings/*.sls $(DESTDIR)/srv/salt/ceph/tests/keyrings
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/tests/openstack
	install -m 644 srv/salt/ceph/tests/openstack/*.sls $(DESTDIR)/srv/salt/ceph/tests/openstack
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/tests/orchestrator
	install -m 644 srv/salt/ceph/tests/orchestrator/*.sls $(DESTDIR)/srv/salt/ceph/tests/orchestrator
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/tests/os_switch
	install -m 644 srv/salt/ceph/tests/os_switch/*.sls $(DESTDIR)/srv/salt/ceph/tests/os_switch
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/tests/quiescent
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/tests/quiescent/timeout
	install -m 644 srv/salt/ceph/tests/quiescent/*.sls $(DESTDIR)/srv/salt/ceph/tests/quiescent
	install -m 644 srv/salt/ceph/tests/quiescent/timeout/*.sls $(DESTDIR)/srv/salt/ceph/tests/quiescent/timeout
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/tests/migrate
	install -m 644 srv/salt/ceph/tests/migrate/*.sls $(DESTDIR)/srv/salt/ceph/tests/migrate
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/tests/remove
	install -m 644 srv/salt/ceph/tests/remove/*.sls $(DESTDIR)/srv/salt/ceph/tests/remove
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/tests/replace
	install -m 644 srv/salt/ceph/tests/replace/*.sls $(DESTDIR)/srv/salt/ceph/tests/replace
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/tests/restart
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/tests/restart/mon
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/tests/restart/mon/change
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/tests/restart/mon/forced
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/tests/restart/mon/nochange
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/tests/restart/mds
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/tests/restart/mds/change
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/tests/restart/mds/forced
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/tests/restart/mds/nochange
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/tests/restart/mgr
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/tests/restart/mgr/change
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/tests/restart/mgr/forced
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/tests/restart/mgr/nochange
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/tests/restart/rgw
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/tests/restart/rgw/change
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/tests/restart/rgw/forced
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/tests/restart/rgw/nochange
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/tests/tuned
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/tests/tuned/off
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/tests/symlink
	install -m 644 srv/salt/ceph/tests/restart/*.sls $(DESTDIR)/srv/salt/ceph/tests/restart
	install -m 644 srv/salt/ceph/tests/restart/mon/*.sls $(DESTDIR)/srv/salt/ceph/tests/restart/mon
	install -m 644 srv/salt/ceph/tests/restart/mon/change/*.sls $(DESTDIR)/srv/salt/ceph/tests/restart/mon/change
	install -m 644 srv/salt/ceph/tests/restart/mon/forced/*.sls $(DESTDIR)/srv/salt/ceph/tests/restart/mon/forced
	install -m 644 srv/salt/ceph/tests/restart/mon/nochange/*.sls $(DESTDIR)/srv/salt/ceph/tests/restart/mon/nochange
	install -m 644 srv/salt/ceph/tests/restart/mds/*.sls $(DESTDIR)/srv/salt/ceph/tests/restart/mds
	install -m 644 srv/salt/ceph/tests/restart/mds/change/*.sls $(DESTDIR)/srv/salt/ceph/tests/restart/mds/change
	install -m 644 srv/salt/ceph/tests/restart/mds/forced/*.sls $(DESTDIR)/srv/salt/ceph/tests/restart/mds/forced
	install -m 644 srv/salt/ceph/tests/restart/mds/nochange/*.sls $(DESTDIR)/srv/salt/ceph/tests/restart/mds/nochange
	install -m 644 srv/salt/ceph/tests/restart/mgr/*.sls $(DESTDIR)/srv/salt/ceph/tests/restart/mgr
	install -m 644 srv/salt/ceph/tests/restart/mgr/change/*.sls $(DESTDIR)/srv/salt/ceph/tests/restart/mgr/change
	install -m 644 srv/salt/ceph/tests/restart/mgr/forced/*.sls $(DESTDIR)/srv/salt/ceph/tests/restart/mgr/forced
	install -m 644 srv/salt/ceph/tests/restart/mgr/nochange/*.sls $(DESTDIR)/srv/salt/ceph/tests/restart/mgr/nochange
	install -m 644 srv/salt/ceph/tests/restart/rgw/*.sls $(DESTDIR)/srv/salt/ceph/tests/restart/rgw
	install -m 644 srv/salt/ceph/tests/restart/rgw/change/*.sls $(DESTDIR)/srv/salt/ceph/tests/restart/rgw/change
	install -m 644 srv/salt/ceph/tests/restart/rgw/forced/*.sls $(DESTDIR)/srv/salt/ceph/tests/restart/rgw/forced
	install -m 644 srv/salt/ceph/tests/restart/rgw/nochange/*.sls $(DESTDIR)/srv/salt/ceph/tests/restart/rgw/nochange
	install -m 644 srv/salt/ceph/tests/tuned/*.sls $(DESTDIR)/srv/salt/ceph/tests/tuned
	install -m 644 srv/salt/ceph/tests/tuned/off/*.sls $(DESTDIR)/srv/salt/ceph/tests/tuned/off
	install -m 644 srv/salt/ceph/tests/symlink/*.sls $(DESTDIR)/srv/salt/ceph/tests/symlink
	# functests/1node
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/functests/1node
	install -m 644 srv/salt/ceph/functests/1node/*.sls $(DESTDIR)/srv/salt/ceph/functests/1node
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/functests/1node/apparmor
	install -m 644 srv/salt/ceph/functests/1node/apparmor/*.sls $(DESTDIR)/srv/salt/ceph/functests/1node/apparmor
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/functests/1node/keyrings
	install -m 644 srv/salt/ceph/functests/1node/keyrings/*.sls $(DESTDIR)/srv/salt/ceph/functests/1node/keyrings
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/functests/1node/macros
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/functests/1node/macros/os_switch
	install -m 644 srv/salt/ceph/functests/1node/macros/os_switch/*.sls $(DESTDIR)/srv/salt/ceph/functests/1node/macros/os_switch
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/functests/1node/openstack
	install -m 644 srv/salt/ceph/functests/1node/openstack/*.sls $(DESTDIR)/srv/salt/ceph/functests/1node/openstack
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/functests/1node/orchestrator
	install -m 644 srv/salt/ceph/functests/1node/orchestrator/*.sls $(DESTDIR)/srv/salt/ceph/functests/1node/orchestrator
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/functests/1node/quiescent
	install -m 644 srv/salt/ceph/functests/1node/quiescent/*.sls $(DESTDIR)/srv/salt/ceph/functests/1node/quiescent
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/functests/1node/migrate
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/functests/1node/migrate/filestore
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/functests/1node/migrate/filestore2
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/functests/1node/migrate/bluestore
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/functests/1node/migrate/bluestore2
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/functests/1node/migrate/bluestore3
	install -m 644 srv/salt/ceph/functests/1node/migrate/*.sls $(DESTDIR)/srv/salt/ceph/functests/1node/migrate
	install -m 644 srv/salt/ceph/functests/1node/migrate/filestore/*.sls $(DESTDIR)/srv/salt/ceph/functests/1node/migrate/filestore
	install -m 644 srv/salt/ceph/functests/1node/migrate/filestore2/*.sls $(DESTDIR)/srv/salt/ceph/functests/1node/migrate/filestore2
	install -m 644 srv/salt/ceph/functests/1node/migrate/bluestore/*.sls $(DESTDIR)/srv/salt/ceph/functests/1node/migrate/bluestore
	install -m 644 srv/salt/ceph/functests/1node/migrate/bluestore2/*.sls $(DESTDIR)/srv/salt/ceph/functests/1node/migrate/bluestore2
	install -m 644 srv/salt/ceph/functests/1node/migrate/bluestore3/*.sls $(DESTDIR)/srv/salt/ceph/functests/1node/migrate/bluestore3
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/functests/1node/rebuild
	install -m 644 srv/salt/ceph/functests/1node/rebuild/*.sls $(DESTDIR)/srv/salt/ceph/functests/1node/rebuild
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/functests/1node/replace
	install -m 644 srv/salt/ceph/functests/1node/replace/*.sls $(DESTDIR)/srv/salt/ceph/functests/1node/replace
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/functests/1node/remove
	install -m 644 srv/salt/ceph/functests/1node/remove/*.sls $(DESTDIR)/srv/salt/ceph/functests/1node/remove
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/functests/1node/restart
	install -m 644 srv/salt/ceph/functests/1node/restart/*.sls $(DESTDIR)/srv/salt/ceph/functests/1node/restart
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/functests/1node/terminate
	install -m 644 srv/salt/ceph/functests/1node/terminate/*.sls $(DESTDIR)/srv/salt/ceph/functests/1node/terminate
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/functests/1node/tuned/off
	install -m 644 srv/salt/ceph/functests/1node/tuned/*.sls $(DESTDIR)/srv/salt/ceph/functests/1node/tuned
	install -m 644 srv/salt/ceph/functests/1node/tuned/off/*.sls $(DESTDIR)/srv/salt/ceph/functests/1node/tuned/off
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/functests/1node/symlink
	install -m 644 srv/salt/ceph/functests/1node/symlink/*.sls $(DESTDIR)/srv/salt/ceph/functests/1node/symlink
	# docs
	install -d -m 755 $(DESTDIR)$(DOCDIR)/deepsea
	install -m 644 LICENSE $(DESTDIR)$(DOCDIR)/deepsea/
	install -m 644 README.md $(DESTDIR)$(DOCDIR)/deepsea/
	# examples
	install -d -m 755 $(DESTDIR)$(DOCDIR)/deepsea/examples
	install -m 644 doc/examples/* $(DESTDIR)$(DOCDIR)/deepsea/examples/
	# pillar
	install -d -m 755 $(DESTDIR)$(DOCDIR)/deepsea/pillar
	install -m 644 doc/pillar/* $(DESTDIR)$(DOCDIR)/deepsea/pillar/
	# stacky.py (included in salt 2016.3)
	install -d -m 755 $(DESTDIR)/srv/modules/pillar
	install -m 644 srv/modules/pillar/stack.py $(DESTDIR)/srv/modules/pillar/
	# modules
	install -d -m 755 $(DESTDIR)/srv/modules/modules
	install -m 644 srv/modules/modules/*.py* $(DESTDIR)/srv/modules/modules/
	# runners
	install -d -m 755 $(DESTDIR)/srv/modules/runners
	install -m 644 srv/modules/runners/*.py* $(DESTDIR)/srv/modules/runners/
	sed -i "s/DEVVERSION/"$(VERSION)"/" $(DESTDIR)/srv/modules/runners/deepsea.py
	# utils
	install -d -m 755 $(DESTDIR)/srv/modules/utils
	install -m 644 srv/modules/utils/*.py* $(DESTDIR)/srv/modules/utils
	# pillar
	install -d -m 755 $(DESTDIR)/srv/pillar/ceph
	install -d -m 755 $(DESTDIR)/srv/pillar/ceph/benchmarks
	install -m 644 srv/pillar/ceph/benchmarks/config.yml $(DESTDIR)/srv/pillar/ceph/benchmarks/config.yml
	install -m 644 srv/pillar/ceph/benchmarks/benchmark.cfg $(DESTDIR)/srv/pillar/ceph/benchmarks/benchmark.cfg
	install -d -m 755 $(DESTDIR)/srv/pillar/ceph/benchmarks/collections
	install -m 644 srv/pillar/ceph/benchmarks/collections/*.yml $(DESTDIR)/srv/pillar/ceph/benchmarks/collections
	install -d -m 755 $(DESTDIR)/srv/pillar/ceph/benchmarks/fio
	install -m 644 srv/pillar/ceph/benchmarks/fio/*.yml $(DESTDIR)/srv/pillar/ceph/benchmarks/fio/
	install -d -m 755 $(DESTDIR)/srv/pillar/ceph/benchmarks/templates
	install -m 644 srv/pillar/ceph/benchmarks/templates/*.j2 $(DESTDIR)/srv/pillar/ceph/benchmarks/templates/
	install -m 644 srv/pillar/ceph/README $(DESTDIR)/srv/pillar/ceph/
	install -m 644 srv/pillar/ceph/init.sls $(DESTDIR)/srv/pillar/ceph/
	install -m 644 srv/pillar/ceph/deepsea_minions.sls $(DESTDIR)/srv/pillar/ceph/
	install -m 644 srv/pillar/ceph/blacklist.sls $(DESTDIR)/srv/pillar/ceph/
	install -m 644 srv/pillar/ceph/disk_led.sls $(DESTDIR)/srv/pillar/ceph/
	install -d -m 755 $(DESTDIR)/srv/pillar/ceph/stack
	install -m 644 srv/pillar/ceph/stack/stack.cfg $(DESTDIR)/srv/pillar/ceph/stack/stack.cfg
	install -m 644 srv/pillar/top.sls $(DESTDIR)/srv/pillar/
	# man pages
	install -d -m 755 $(DESTDIR)/usr/share/man/man7
	install -m 644 man/deepsea*.7 $(DESTDIR)/usr/share/man/man7
	install -d -m 755 $(DESTDIR)/usr/share/man/man5
	install -m 644 man/deepsea*.5 $(DESTDIR)/usr/share/man/man5
	install -d -m 755 $(DESTDIR)/usr/share/man/man1
	install -m 644 man/deepsea*.1 $(DESTDIR)/usr/share/man/man1
	# modules
	install -d -m 755 $(DESTDIR)/srv/salt/_modules
	install -m 644 srv/salt/_modules/*.py* $(DESTDIR)/srv/salt/_modules/
	# state modules
	install -d -m 755 $(DESTDIR)/srv/salt/_states
	install -m 644 srv/salt/_states/*.py* $(DESTDIR)/srv/salt/_states/
	# state files
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/admin
	install -m 644 srv/salt/ceph/admin/*.sls $(DESTDIR)/srv/salt/ceph/admin/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/admin/key
	install -m 644 srv/salt/ceph/admin/key/*.sls $(DESTDIR)/srv/salt/ceph/admin/key/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/admin/files
	install -m 644 srv/salt/ceph/admin/files/*.j2 $(DESTDIR)/srv/salt/ceph/admin/files/
	# state files apparmor
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/apparmor
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/apparmor/files
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/apparmor/files/ceph.d
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/apparmor/install
	install -m 644 srv/salt/ceph/apparmor/*.sls $(DESTDIR)/srv/salt/ceph/apparmor/
	install -m 644 srv/salt/ceph/apparmor/files/usr* $(DESTDIR)/srv/salt/ceph/apparmor/files/
	install -m 644 srv/salt/ceph/apparmor/files/ceph.d/* $(DESTDIR)/srv/salt/ceph/apparmor/files/ceph.d/
	install -m 644 srv/salt/ceph/apparmor/install/*.sls $(DESTDIR)/srv/salt/ceph/apparmor/install/
	# state files benchmarks
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/benchmarks
	install -m 644 srv/salt/ceph/benchmarks/*.sls $(DESTDIR)/srv/salt/ceph/benchmarks/
	# state files cephfs
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/cephfs
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/cephfs/benchmarks
	install -m 644 srv/salt/ceph/cephfs/benchmarks/*.sls $(DESTDIR)/srv/salt/ceph/cephfs/benchmarks/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/cephfs/benchmarks/files
	install -m 644 srv/salt/ceph/cephfs/benchmarks/files/keyring.j2 $(DESTDIR)/srv/salt/ceph/cephfs/benchmarks/files/
	# state files tools
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/tools/fio
	install -m 644 srv/salt/ceph/tools/fio/*.sls $(DESTDIR)/srv/salt/ceph/tools/fio
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/tools/fio/files
	install -m 644 srv/salt/ceph/tools/fio/files/fio.service $(DESTDIR)/srv/salt/ceph/tools/fio/files
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/tools/benchmarks
	install -m 644 srv/salt/ceph/tools/benchmarks/*.sls $(DESTDIR)/srv/salt/ceph/tools/benchmarks
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/configuration
	install -m 644 srv/salt/ceph/configuration/*.sls $(DESTDIR)/srv/salt/ceph/configuration/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/configuration/check
	install -m 644 srv/salt/ceph/configuration/check/*.sls $(DESTDIR)/srv/salt/ceph/configuration/check/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/configuration/create
	install -m 644 srv/salt/ceph/configuration/create/*.sls $(DESTDIR)/srv/salt/ceph/configuration/create/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/configuration/files
	install -m 644 srv/salt/ceph/configuration/files/*.j2 $(DESTDIR)/srv/salt/ceph/configuration/files/
	install -m 644 srv/salt/ceph/configuration/files/rbd.conf $(DESTDIR)/srv/salt/ceph/configuration/files/
	install -m 644 srv/salt/ceph/configuration/files/rgw.conf $(DESTDIR)/srv/salt/ceph/configuration/files/
	install -m 644 srv/salt/ceph/configuration/files/rgw-ssl.conf $(DESTDIR)/srv/salt/ceph/configuration/files/
	install -m 644 srv/salt/ceph/configuration/files/ceph.conf.import $(DESTDIR)/srv/salt/ceph/configuration/files/
	install -m 644 srv/salt/ceph/configuration/files/drive_groups.yml $(DESTDIR)/srv/salt/ceph/configuration/files/
	install -m 644 srv/salt/ceph/configuration/files/deprecated_map.yml $(DESTDIR)/srv/salt/ceph/configuration/files/
	-chown salt:salt $(DESTDIR)/srv/salt/ceph/configuration/files/ceph.conf.import || true
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/configuration/files/ceph.conf.d
	install -m 644 srv/salt/ceph/configuration/files/ceph.conf.d/README $(DESTDIR)/srv/salt/ceph/configuration/files/ceph.conf.d
	# state files - ganesha
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/ganesha
	install -m 644 srv/salt/ceph/ganesha/*.sls $(DESTDIR)/srv/salt/ceph/ganesha/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/ganesha/auth
	install -m 644 srv/salt/ceph/ganesha/auth/*.sls $(DESTDIR)/srv/salt/ceph/ganesha/auth
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/ganesha/files
	install -m 644 srv/salt/ceph/ganesha/files/*.j2 $(DESTDIR)/srv/salt/ceph/ganesha/files
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
	install -m 644 srv/salt/ceph/ganesha/restart/*.sls $(DESTDIR)/srv/salt/ceph/ganesha/restart/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/ganesha/restart/force
	install -m 644 srv/salt/ceph/ganesha/restart/force/*.sls $(DESTDIR)/srv/salt/ceph/ganesha/restart/force
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/ganesha/restart/controlled
	install -m 644 srv/salt/ceph/ganesha/restart/controlled/*.sls $(DESTDIR)/srv/salt/ceph/ganesha/restart/controlled
	# state files - igw
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/igw
	install -m 644 srv/salt/ceph/igw/*.sls $(DESTDIR)/srv/salt/ceph/igw/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/igw/files
	install -m 644 srv/salt/ceph/igw/files/*.j2 $(DESTDIR)/srv/salt/ceph/igw/files/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/igw/config
	install -m 644 srv/salt/ceph/igw/config/*.sls $(DESTDIR)/srv/salt/ceph/igw/config/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/igw/key
	install -m 644 srv/salt/ceph/igw/key/*.sls $(DESTDIR)/srv/salt/ceph/igw/key/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/igw/auth
	install -m 644 srv/salt/ceph/igw/auth/*.sls $(DESTDIR)/srv/salt/ceph/igw/auth/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/igw/keyring
	install -m 644 srv/salt/ceph/igw/keyring/*.sls $(DESTDIR)/srv/salt/ceph/igw/keyring/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/igw/restart
	install -m 644 srv/salt/ceph/igw/restart/*.sls $(DESTDIR)/srv/salt/ceph/igw/restart
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/igw/restart/force
	install -m 644 srv/salt/ceph/igw/restart/force/*.sls $(DESTDIR)/srv/salt/ceph/igw/restart/force
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/igw/restart/controlled
	install -m 644 srv/salt/ceph/igw/restart/controlled/*.sls $(DESTDIR)/srv/salt/ceph/igw/restart/controlled
	# state files - macros
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/macros
	install -m 644 srv/salt/ceph/macros/*.sls $(DESTDIR)/srv/salt/ceph/macros/
	# state files - dashboard
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/dashboard
	install -m 644 srv/salt/ceph/dashboard/*.sls $(DESTDIR)/srv/salt/ceph/dashboard/
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
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/mds/restart/force
	install -m 644 srv/salt/ceph/mds/restart/force/*.sls $(DESTDIR)/srv/salt/ceph/mds/restart/force
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/mds/restart/controlled
	install -m 644 srv/salt/ceph/mds/restart/controlled/*.sls $(DESTDIR)/srv/salt/ceph/mds/restart/controlled
	# state files - metapackage
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/metapackage
	install -m 644 srv/salt/ceph/metapackage/*.sls $(DESTDIR)/srv/salt/ceph/metapackage/
	# state files - mgr
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/mgr
	install -m 644 srv/salt/ceph/mgr/*.sls $(DESTDIR)/srv/salt/ceph/mgr/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/mgr/key
	install -m 644 srv/salt/ceph/mgr/key/*.sls $(DESTDIR)/srv/salt/ceph/mgr/key/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/mgr/dashboard
	install -m 644 srv/salt/ceph/mgr/dashboard/*.sls $(DESTDIR)/srv/salt/ceph/mgr/dashboard/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/mgr/auth
	install -m 644 srv/salt/ceph/mgr/auth/*.sls $(DESTDIR)/srv/salt/ceph/mgr/auth/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/mgr/keyring
	install -m 644 srv/salt/ceph/mgr/keyring/*.sls $(DESTDIR)/srv/salt/ceph/mgr/keyring/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/mgr/files
	install -m 644 srv/salt/ceph/mgr/files/*.j2 $(DESTDIR)/srv/salt/ceph/mgr/files/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/mgr/orchestrator
	install -m 644 srv/salt/ceph/mgr/orchestrator/*.sls $(DESTDIR)/srv/salt/ceph/mgr/orchestrator/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/mgr/restart
	install -m 644 srv/salt/ceph/mgr/restart/*.sls $(DESTDIR)/srv/salt/ceph/mgr/restart
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/mgr/restart/force
	install -m 644 srv/salt/ceph/mgr/restart/force/default.sls $(DESTDIR)/srv/salt/ceph/mgr/restart/force
	install -m 644 srv/salt/ceph/mgr/restart/force/init.sls $(DESTDIR)/srv/salt/ceph/mgr/restart/force
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/mgr/restart/controlled
	install -m 644 srv/salt/ceph/mgr/restart/controlled/default.sls $(DESTDIR)/srv/salt/ceph/mgr/restart/controlled
	install -m 644 srv/salt/ceph/mgr/restart/controlled/init.sls $(DESTDIR)/srv/salt/ceph/mgr/restart/controlled
	# state files - salt-api
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/salt-api
	install -m 644 srv/salt/ceph/salt-api/*.sls $(DESTDIR)/srv/salt/ceph/salt-api
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/salt-api/files
	install -m 644 srv/salt/ceph/salt-api/files/*.conf* $(DESTDIR)/srv/salt/ceph/salt-api/files

	# state files - migrate
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/migrate
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/migrate/osds
	install -m 644 srv/salt/ceph/migrate/osds/*.sls $(DESTDIR)/srv/salt/ceph/migrate/osds/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/migrate/nodes
	install -m 644 srv/salt/ceph/migrate/nodes/*.sls $(DESTDIR)/srv/salt/ceph/migrate/nodes/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/migrate/policy
	install -m 644 srv/salt/ceph/migrate/policy/*.sls $(DESTDIR)/srv/salt/ceph/migrate/policy/
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
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/mon/restart/force
	install -m 644 srv/salt/ceph/mon/restart/force/default.sls $(DESTDIR)/srv/salt/ceph/mon/restart/force
	install -m 644 srv/salt/ceph/mon/restart/force/init.sls $(DESTDIR)/srv/salt/ceph/mon/restart/force
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/mon/restart/controlled
	install -m 644 srv/salt/ceph/mon/restart/controlled/default.sls $(DESTDIR)/srv/salt/ceph/mon/restart/controlled
	install -m 644 srv/salt/ceph/mon/restart/controlled/init.sls $(DESTDIR)/srv/salt/ceph/mon/restart/controlled
	# state files - monitoring
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/monitoring
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/monitoring/alertmanager
	install -m 644 srv/salt/ceph/monitoring/alertmanager/*.sls $(DESTDIR)/srv/salt/ceph/monitoring/alertmanager
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/monitoring/alertmanager/files
	install -m 644 srv/salt/ceph/monitoring/alertmanager/files/*.j2 $(DESTDIR)/srv/salt/ceph/monitoring/alertmanager/files
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/monitoring/grafana
	install -m 644 srv/salt/ceph/monitoring/grafana/*.sls $(DESTDIR)/srv/salt/ceph/monitoring/grafana
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/monitoring/grafana/files
	install -m 644 srv/salt/ceph/monitoring/grafana/files/*.j2 $(DESTDIR)/srv/salt/ceph/monitoring/grafana/files
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/monitoring/prometheus
	install -m 644 srv/salt/ceph/monitoring/prometheus/*.sls $(DESTDIR)/srv/salt/ceph/monitoring/prometheus
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/monitoring/prometheus/files
	install -m 644 srv/salt/ceph/monitoring/prometheus/files/*.j2 $(DESTDIR)/srv/salt/ceph/monitoring/prometheus/files
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/monitoring/prometheus/exporters
	install -m 644 srv/salt/ceph/monitoring/prometheus/exporters/*.sls $(DESTDIR)/srv/salt/ceph/monitoring/prometheus/exporters
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/monitoring/prometheus/exporters/files
	install -m 644 srv/salt/ceph/monitoring/prometheus/exporters/files/* $(DESTDIR)/srv/salt/ceph/monitoring/prometheus/exporters/files
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/monitoring/prometheus/exporters/ceph_rgw_exporter
	install -m 644 srv/salt/ceph/monitoring/prometheus/exporters/ceph_rgw_exporter/*.sls $(DESTDIR)/srv/salt/ceph/monitoring/prometheus/exporters/ceph_rgw_exporter
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/monitoring/prometheus/exporters/ceph_rgw_exporter/CentOS
	install -m 644 srv/salt/ceph/monitoring/prometheus/exporters/ceph_rgw_exporter/CentOS/*.sls $(DESTDIR)/srv/salt/ceph/monitoring/prometheus/exporters/ceph_rgw_exporter/CentOS
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/monitoring/prometheus/exporters/ceph_rgw_exporter/SLES-15
	install -m 644 srv/salt/ceph/monitoring/prometheus/exporters/ceph_rgw_exporter/SLES-15/*.sls $(DESTDIR)/srv/salt/ceph/monitoring/prometheus/exporters/ceph_rgw_exporter/SLES-15
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/monitoring/prometheus/exporters/ceph_rgw_exporter/cron
	install -m 644 srv/salt/ceph/monitoring/prometheus/exporters/ceph_rgw_exporter/cron/*.sls $(DESTDIR)/srv/salt/ceph/monitoring/prometheus/exporters/ceph_rgw_exporter/cron
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/monitoring/prometheus/exporters/ceph_rgw_exporter/files
	install -m 644 srv/salt/ceph/monitoring/prometheus/exporters/ceph_rgw_exporter/files/*.py $(DESTDIR)/srv/salt/ceph/monitoring/prometheus/exporters/ceph_rgw_exporter/files
	# state files - noout
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/noout
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/noout/set
	install -m 644 srv/salt/ceph/noout/set/*.sls $(DESTDIR)/srv/salt/ceph/noout/set
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/noout/unset
	install -m 644 srv/salt/ceph/noout/unset/*.sls $(DESTDIR)/srv/salt/ceph/noout/unset
	# state files - openstack
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/openstack
	install -m 644 srv/salt/ceph/openstack/*.sls $(DESTDIR)/srv/salt/ceph/openstack/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/openstack/cinder
	install -m 644 srv/salt/ceph/openstack/cinder/*.sls $(DESTDIR)/srv/salt/ceph/openstack/cinder
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/openstack/cinder/auth
	install -m 644 srv/salt/ceph/openstack/cinder/auth/*.sls $(DESTDIR)/srv/salt/ceph/openstack/cinder/auth
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/openstack/cinder/files
	install -m 644 srv/salt/ceph/openstack/cinder/files/*.j2 $(DESTDIR)/srv/salt/ceph/openstack/cinder/files
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/openstack/cinder/key
	install -m 644 srv/salt/ceph/openstack/cinder/key/*.sls $(DESTDIR)/srv/salt/ceph/openstack/cinder/key
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/openstack/cinder/pool
	install -m 644 srv/salt/ceph/openstack/cinder/pool/*.sls $(DESTDIR)/srv/salt/ceph/openstack/cinder/pool
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/openstack/cinder-backup
	install -m 644 srv/salt/ceph/openstack/cinder-backup/*.sls $(DESTDIR)/srv/salt/ceph/openstack/cinder-backup
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/openstack/cinder-backup/auth
	install -m 644 srv/salt/ceph/openstack/cinder-backup/auth/*.sls $(DESTDIR)/srv/salt/ceph/openstack/cinder-backup/auth
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/openstack/cinder-backup/files
	install -m 644 srv/salt/ceph/openstack/cinder-backup/files/*.j2 $(DESTDIR)/srv/salt/ceph/openstack/cinder-backup/files
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/openstack/cinder-backup/key
	install -m 644 srv/salt/ceph/openstack/cinder-backup/key/*.sls $(DESTDIR)/srv/salt/ceph/openstack/cinder-backup/key
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/openstack/cinder-backup/pool
	install -m 644 srv/salt/ceph/openstack/cinder-backup/pool/*.sls $(DESTDIR)/srv/salt/ceph/openstack/cinder-backup/pool
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/openstack/glance
	install -m 644 srv/salt/ceph/openstack/glance/*.sls $(DESTDIR)/srv/salt/ceph/openstack/glance
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/openstack/glance/auth
	install -m 644 srv/salt/ceph/openstack/glance/auth/*.sls $(DESTDIR)/srv/salt/ceph/openstack/glance/auth
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/openstack/glance/files
	install -m 644 srv/salt/ceph/openstack/glance/files/*.j2 $(DESTDIR)/srv/salt/ceph/openstack/glance/files
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/openstack/glance/key
	install -m 644 srv/salt/ceph/openstack/glance/key/*.sls $(DESTDIR)/srv/salt/ceph/openstack/glance/key
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/openstack/glance/pool
	install -m 644 srv/salt/ceph/openstack/glance/pool/*.sls $(DESTDIR)/srv/salt/ceph/openstack/glance/pool
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/openstack/nova
	install -m 644 srv/salt/ceph/openstack/nova/*.sls $(DESTDIR)/srv/salt/ceph/openstack/nova
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/openstack/nova/pool
	install -m 644 srv/salt/ceph/openstack/nova/pool/*.sls $(DESTDIR)/srv/salt/ceph/openstack/nova/pool
	# state files - osd
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/osd
	install -m 644 srv/salt/ceph/osd/*.sls $(DESTDIR)/srv/salt/ceph/osd/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/osd/key
	install -m 644 srv/salt/ceph/osd/key/*.sls $(DESTDIR)/srv/salt/ceph/osd/key/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/osd/auth
	install -m 644 srv/salt/ceph/osd/auth/*.sls $(DESTDIR)/srv/salt/ceph/osd/auth/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/osd/keyring
	install -m 644 srv/salt/ceph/osd/keyring/*.sls $(DESTDIR)/srv/salt/ceph/osd/keyring/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/osd/scheduler
	install -m 644 srv/salt/ceph/osd/scheduler/*.sls $(DESTDIR)/srv/salt/ceph/osd/scheduler/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/osd/takeover
	install -m 644 srv/salt/ceph/osd/takeover/*.sls $(DESTDIR)/srv/salt/ceph/osd/takeover/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/osd/files
	install -m 644 srv/salt/ceph/osd/files/*.j2 $(DESTDIR)/srv/salt/ceph/osd/files/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/osd/restart
	install -m 644 srv/salt/ceph/osd/restart/default.sls $(DESTDIR)/srv/salt/ceph/osd/restart
	install -m 644 srv/salt/ceph/osd/restart/init.sls $(DESTDIR)/srv/salt/ceph/osd/restart
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/osd/restart/force
	install -m 644 srv/salt/ceph/osd/restart/force/default.sls $(DESTDIR)/srv/salt/ceph/osd/restart/force
	install -m 644 srv/salt/ceph/osd/restart/force/init.sls $(DESTDIR)/srv/salt/ceph/osd/restart/force
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/osd/restart/controlled
	install -m 644 srv/salt/ceph/osd/restart/controlled/default.sls $(DESTDIR)/srv/salt/ceph/osd/restart/controlled
	install -m 644 srv/salt/ceph/osd/restart/controlled/init.sls $(DESTDIR)/srv/salt/ceph/osd/restart/controlled
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/osd/restart/parallel
	install -m 644 srv/salt/ceph/osd/restart/parallel/default.sls $(DESTDIR)/srv/salt/ceph/osd/restart/parallel
	install -m 644 srv/salt/ceph/osd/restart/parallel/init.sls $(DESTDIR)/srv/salt/ceph/osd/restart/parallel
	# state files - packages
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/packages
	install -m 644 srv/salt/ceph/packages/*.sls $(DESTDIR)/srv/salt/ceph/packages/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/packages/common
	install -m 644 srv/salt/ceph/packages/common/*.sls $(DESTDIR)/srv/salt/ceph/packages/common/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/packages/remove
	install -m 644 srv/salt/ceph/packages/remove/*.sls $(DESTDIR)/srv/salt/ceph/packages/remove/
	# state files - pool
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/pool
	install -m 644 srv/salt/ceph/pool/*.sls $(DESTDIR)/srv/salt/ceph/pool/
	# state files - purge
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/purge
	install -m 644 srv/salt/ceph/purge/*.sls $(DESTDIR)/srv/salt/ceph/purge/
	# state files - rbd
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/rbd
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/rbd/benchmarks
	install -m 644 srv/salt/ceph/rbd/benchmarks/*.sls $(DESTDIR)/srv/salt/ceph/rbd/benchmarks/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/rbd/benchmarks/files
	install -m 644 srv/salt/ceph/rbd/benchmarks/files/keyring.j2 $(DESTDIR)/srv/salt/ceph/rbd/benchmarks/files/
	# state files - benchmark-blockdev
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/benchmarks/blockdev/
	install -m 644 srv/salt/ceph/benchmarks/blockdev/*.sls $(DESTDIR)/srv/salt/ceph/benchmarks/blockdev/
	# state files - benchmark-fs
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/benchmarks/fs/
	install -m 644 srv/salt/ceph/benchmarks/fs/*.sls $(DESTDIR)/srv/salt/ceph/benchmarks/fs/
	# state files - reactor
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/reactor
	install -m 644 srv/salt/ceph/reactor/*.sls $(DESTDIR)/srv/salt/ceph/reactor/
	# state files - refresh
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/refresh
	install -m 644 srv/salt/ceph/refresh/*.sls $(DESTDIR)/srv/salt/ceph/refresh/
	# state files - redeploy
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/redeploy
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/redeploy/osds
	install -m 644 srv/salt/ceph/redeploy/osds/*.sls $(DESTDIR)/srv/salt/ceph/redeploy/osds/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/redeploy/nodes
	install -m 644 srv/salt/ceph/redeploy/nodes/*.sls $(DESTDIR)/srv/salt/ceph/redeploy/nodes/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/redeploy/nodes
	# state files - remove
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/remove
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/remove/igw/auth
	install -m 644 srv/salt/ceph/remove/igw/auth/*.sls $(DESTDIR)/srv/salt/ceph/remove/igw/auth/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/remove/mds
	install -m 644 srv/salt/ceph/remove/mds/*.sls $(DESTDIR)/srv/salt/ceph/remove/mds/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/remove/destroyed
	install -m 644 srv/salt/ceph/remove/destroyed/*.sls $(DESTDIR)/srv/salt/ceph/remove/destroyed/
	# Renamed for deprecation
	ln -sf destroyed	$(DESTDIR)/srv/salt/ceph/remove/migrated
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/remove/mgr
	install -m 644 srv/salt/ceph/remove/mgr/*.sls $(DESTDIR)/srv/salt/ceph/remove/mgr/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/remove/mon
	install -m 644 srv/salt/ceph/remove/mon/*.sls $(DESTDIR)/srv/salt/ceph/remove/mon/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/remove/rgw
	install -m 644 srv/salt/ceph/remove/rgw/*.sls $(DESTDIR)/srv/salt/ceph/remove/rgw/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/remove/ganesha
	install -m 644 srv/salt/ceph/remove/ganesha/*.sls $(DESTDIR)/srv/salt/ceph/remove/ganesha/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/remove/storage
	install -m 644 srv/salt/ceph/remove/storage/*.sls $(DESTDIR)/srv/salt/ceph/remove/storage/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/remove/storage/drain
	install -m 644 srv/salt/ceph/remove/storage/drain/*.sls $(DESTDIR)/srv/salt/ceph/remove/storage/drain
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/remove/openattic
	install -m 644 srv/salt/ceph/remove/openattic/*.sls $(DESTDIR)/srv/salt/ceph/remove/openattic/
	# state files - rescind
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/rescind
	install -m 644 srv/salt/ceph/rescind/*.sls $(DESTDIR)/srv/salt/ceph/rescind/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/rescind/alertmanager
	install -m 644 srv/salt/ceph/rescind/alertmanager/*.sls $(DESTDIR)/srv/salt/ceph/rescind/alertmanager/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/rescind/admin
	install -m 644 srv/salt/ceph/rescind/admin/*.sls $(DESTDIR)/srv/salt/ceph/rescind/admin/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/rescind/configuration
	install -m 644 srv/salt/ceph/rescind/configuration/*.sls $(DESTDIR)/srv/salt/ceph/rescind/configuration/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/rescind/client-iscsi
	install -m 644 srv/salt/ceph/rescind/client-iscsi/*.sls $(DESTDIR)/srv/salt/ceph/rescind/client-iscsi/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/rescind/ganesha
	install -m 644 srv/salt/ceph/rescind/ganesha/*.sls $(DESTDIR)/srv/salt/ceph/rescind/ganesha/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/rescind/igw
	install -m 644 srv/salt/ceph/rescind/igw/*.sls $(DESTDIR)/srv/salt/ceph/rescind/igw/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/rescind/igw/ceph-iscsi
	install -m 644 srv/salt/ceph/rescind/igw/ceph-iscsi/*.sls $(DESTDIR)/srv/salt/ceph/rescind/igw/ceph-iscsi/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/rescind/igw/keyring
	install -m 644 srv/salt/ceph/rescind/igw/keyring/*.sls $(DESTDIR)/srv/salt/ceph/rescind/igw/keyring/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/rescind/master
	install -m 644 srv/salt/ceph/rescind/master/*.sls $(DESTDIR)/srv/salt/ceph/rescind/master/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/rescind/client-cephfs
	install -m 644 srv/salt/ceph/rescind/client-cephfs/*.sls $(DESTDIR)/srv/salt/ceph/rescind/client-cephfs/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/rescind/client-nfs
	install -m 644 srv/salt/ceph/rescind/client-nfs/*.sls $(DESTDIR)/srv/salt/ceph/rescind/client-nfs/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/rescind/mds
	install -m 644 srv/salt/ceph/rescind/mds/*.sls $(DESTDIR)/srv/salt/ceph/rescind/mds/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/rescind/mds/keyring
	install -m 644 srv/salt/ceph/rescind/mds/keyring/*.sls $(DESTDIR)/srv/salt/ceph/rescind/mds/keyring/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/rescind/mgr
	install -m 644 srv/salt/ceph/rescind/mgr/*.sls $(DESTDIR)/srv/salt/ceph/rescind/mgr/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/rescind/mgr/keyring
	install -m 644 srv/salt/ceph/rescind/mgr/keyring/*.sls $(DESTDIR)/srv/salt/ceph/rescind/mgr/keyring/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/rescind/mgr/dashboard
	install -m 644 srv/salt/ceph/rescind/mgr/dashboard/*.sls $(DESTDIR)/srv/salt/ceph/rescind/mgr/dashboard/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/rescind/mon
	install -m 644 srv/salt/ceph/rescind/mon/*.sls $(DESTDIR)/srv/salt/ceph/rescind/mon/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/rescind/admin
	install -m 644 srv/salt/ceph/rescind/admin/*.sls $(DESTDIR)/srv/salt/ceph/rescind/admin/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/rescind/client-radosgw
	install -m 644 srv/salt/ceph/rescind/client-radosgw/*.sls $(DESTDIR)/srv/salt/ceph/rescind/client-radosgw/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/rescind/benchmark-rbd
	install -m 644 srv/salt/ceph/rescind/benchmark-rbd/*.sls $(DESTDIR)/srv/salt/ceph/rescind/benchmark-rbd/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/rescind/benchmark-blockdev
	install -m 644 srv/salt/ceph/rescind/benchmark-blockdev/*.sls $(DESTDIR)/srv/salt/ceph/rescind/benchmark-blockdev/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/rescind/benchmark-fs
	install -m 644 srv/salt/ceph/rescind/benchmark-fs/*.sls $(DESTDIR)/srv/salt/ceph/rescind/benchmark-fs/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/rescind/rgw
	install -m 644 srv/salt/ceph/rescind/rgw/*.sls $(DESTDIR)/srv/salt/ceph/rescind/rgw/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/rescind/rgw/keyring
	install -m 644 srv/salt/ceph/rescind/rgw/keyring/*.sls $(DESTDIR)/srv/salt/ceph/rescind/rgw/keyring/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/rescind/rgw/monitoring
	install -m 644 srv/salt/ceph/rescind/rgw/monitoring/*.sls $(DESTDIR)/srv/salt/ceph/rescind/rgw/monitoring/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/rescind/storage
	install -m 644 srv/salt/ceph/rescind/storage/*.sls $(DESTDIR)/srv/salt/ceph/rescind/storage/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/rescind/storage/keyring
	install -m 644 srv/salt/ceph/rescind/storage/keyring/*.sls $(DESTDIR)/srv/salt/ceph/rescind/storage/keyring/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/rescind/storage/terminate
	install -m 644 srv/salt/ceph/rescind/storage/terminate/*.sls $(DESTDIR)/srv/salt/ceph/rescind/storage/terminate/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/rescind/time
	install -m 644 srv/salt/ceph/rescind/time/*.sls $(DESTDIR)/srv/salt/ceph/rescind/time/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/rescind/time/chrony
	install -m 644 srv/salt/ceph/rescind/time/chrony/*.sls $(DESTDIR)/srv/salt/ceph/rescind/time/chrony
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/rescind/time/ntp
	install -m 644 srv/salt/ceph/rescind/time/ntp/*.sls $(DESTDIR)/srv/salt/ceph/rescind/time/ntp
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/rescind/tuned
	install -m 644 srv/salt/ceph/rescind/tuned/*.sls $(DESTDIR)/srv/salt/ceph/rescind/tuned/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/rescind/openattic
	install -m 644 srv/salt/ceph/rescind/openattic/*.sls $(DESTDIR)/srv/salt/ceph/rescind/openattic/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/rescind/openattic/keyring
	install -m 644 srv/salt/ceph/rescind/openattic/keyring/*.sls $(DESTDIR)/srv/salt/ceph/rescind/openattic/keyring/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/rescind/grafana
	install -m 644 srv/salt/ceph/rescind/grafana/*.sls $(DESTDIR)/srv/salt/ceph/rescind/grafana/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/rescind/prometheus
	install -m 644 srv/salt/ceph/rescind/prometheus/*.sls $(DESTDIR)/srv/salt/ceph/rescind/prometheus/
	# state files - repo
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/repo
	install -m 644 srv/salt/ceph/repo/*.sls $(DESTDIR)/srv/salt/ceph/repo/
	# state files - restart
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/restart
	install -m 644 srv/salt/ceph/restart/*.sls $(DESTDIR)/srv/salt/ceph/restart/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/restart/force
	install -m 644 srv/salt/ceph/restart/force/*.sls $(DESTDIR)/srv/salt/ceph/restart/force/
	# state files - restart - mon
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/restart/mon
	install -m 644 srv/salt/ceph/restart/mon/*.sls $(DESTDIR)/srv/salt/ceph/restart/mon
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/restart/mon/force
	install -m 644 srv/salt/ceph/restart/mon/force/*.sls $(DESTDIR)/srv/salt/ceph/restart/mon/force
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/restart/mon/lax
	install -m 644 srv/salt/ceph/restart/mon/lax/*.sls $(DESTDIR)/srv/salt/ceph/restart/mon/lax
	# state files - restart - mgr
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/restart/mgr
	install -m 644 srv/salt/ceph/restart/mgr/*.sls $(DESTDIR)/srv/salt/ceph/restart/mgr
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/restart/mgr/force
	install -m 644 srv/salt/ceph/restart/mgr/force/*.sls $(DESTDIR)/srv/salt/ceph/restart/mgr/force
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/restart/mgr/lax
	install -m 644 srv/salt/ceph/restart/mgr/lax/*.sls $(DESTDIR)/srv/salt/ceph/restart/mgr/lax
	# state files - restart - osd
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/restart/osd
	install -m 644 srv/salt/ceph/restart/osd/*.sls $(DESTDIR)/srv/salt/ceph/restart/osd
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/restart/osd/force
	install -m 644 srv/salt/ceph/restart/osd/force/*.sls $(DESTDIR)/srv/salt/ceph/restart/osd/force
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/restart/osd/lax
	install -m 644 srv/salt/ceph/restart/osd/lax/*.sls $(DESTDIR)/srv/salt/ceph/restart/osd/lax
	# state files - restart - rgw
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/restart/rgw
	install -m 644 srv/salt/ceph/restart/rgw/*.sls $(DESTDIR)/srv/salt/ceph/restart/rgw
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/restart/rgw/force
	install -m 644 srv/salt/ceph/restart/rgw/force/*.sls $(DESTDIR)/srv/salt/ceph/restart/rgw/force
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/restart/rgw/lax
	install -m 644 srv/salt/ceph/restart/rgw/lax/*.sls $(DESTDIR)/srv/salt/ceph/restart/rgw/lax
	# state files - restart - mds
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/restart/mds
	install -m 644 srv/salt/ceph/restart/mds/*.sls $(DESTDIR)/srv/salt/ceph/restart/mds
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/restart/mds/force
	install -m 644 srv/salt/ceph/restart/mds/force/*.sls $(DESTDIR)/srv/salt/ceph/restart/mds/force
	# state files - restart - ganesha
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/restart/ganesha
	install -m 644 srv/salt/ceph/restart/ganesha/*.sls $(DESTDIR)/srv/salt/ceph/restart/ganesha
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/restart/ganesha/force
	install -m 644 srv/salt/ceph/restart/ganesha/force/*.sls $(DESTDIR)/srv/salt/ceph/restart/ganesha/force
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/restart/ganesha/lax
	install -m 644 srv/salt/ceph/restart/ganesha/lax/*.sls $(DESTDIR)/srv/salt/ceph/restart/ganesha/lax
	# state files - restart - igw
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/restart/igw
	install -m 644 srv/salt/ceph/restart/igw/*.sls $(DESTDIR)/srv/salt/ceph/restart/igw
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/restart/igw/force
	install -m 644 srv/salt/ceph/restart/igw/force/*.sls $(DESTDIR)/srv/salt/ceph/restart/igw/force
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/restart/igw/lax
	install -m 644 srv/salt/ceph/restart/igw/lax/*.sls $(DESTDIR)/srv/salt/ceph/restart/igw/lax
	# state files - restart - grafana
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/restart/grafana
	install -m 644 srv/salt/ceph/restart/grafana/*.sls $(DESTDIR)/srv/salt/ceph/restart/grafana
	# state files - restart - prometheus
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/restart/prometheus
	install -m 644 srv/salt/ceph/restart/prometheus/*.sls $(DESTDIR)/srv/salt/ceph/restart/prometheus
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
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/rgw/users/users.d
	install -m 644 srv/salt/ceph/rgw/users/users.d/README $(DESTDIR)/srv/salt/ceph/rgw/users/users.d
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/rgw/files
	install -m 644 srv/salt/ceph/rgw/files/*.j2 $(DESTDIR)/srv/salt/ceph/rgw/files/
	install -m 644 srv/salt/ceph/rgw/files/*.yml $(DESTDIR)/srv/salt/ceph/rgw/files/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/rgw/restart
	install -m 644 srv/salt/ceph/rgw/restart/default.sls $(DESTDIR)/srv/salt/ceph/rgw/restart
	install -m 644 srv/salt/ceph/rgw/restart/init.sls $(DESTDIR)/srv/salt/ceph/rgw/restart
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/rgw/restart/force
	install -m 644 srv/salt/ceph/rgw/restart/force/*.sls $(DESTDIR)/srv/salt/ceph/rgw/restart/force
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/rgw/restart/controlled
	install -m 644 srv/salt/ceph/rgw/restart/controlled/*.sls $(DESTDIR)/srv/salt/ceph/rgw/restart/controlled
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/rgw/cert/
	install -m 644 srv/salt/ceph/rgw/cert/*.sls $(DESTDIR)/srv/salt/ceph/rgw/cert/
	# state files - shutdown
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/shutdown
	install -m 644 srv/salt/ceph/shutdown/*.sls $(DESTDIR)/srv/salt/ceph/shutdown
	# state files - ssl
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/ssl
	install -m 644 srv/salt/ceph/ssl/*.sls $(DESTDIR)/srv/salt/ceph/ssl
	# state files - startup
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/startup
	install -m 644 srv/salt/ceph/startup/*.sls $(DESTDIR)/srv/salt/ceph/startup
	# state files - sysctl
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/sysctl
	install -m 644 srv/salt/ceph/sysctl/*.sls $(DESTDIR)/srv/salt/ceph/sysctl
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/sysctl/files
	install -m 644 srv/salt/ceph/sysctl/files/*.conf $(DESTDIR)/srv/salt/ceph/sysctl/files
	# state files - start
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/start
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/start/ganesha
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/start/igw
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/start/mds
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/start/mgr
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/start/mon
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/start/rgw
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/start/storage
	install -m 644 srv/salt/ceph/start/ganesha/*.sls $(DESTDIR)/srv/salt/ceph/start/ganesha
	install -m 644 srv/salt/ceph/start/igw/*.sls $(DESTDIR)/srv/salt/ceph/start/igw
	install -m 644 srv/salt/ceph/start/mds/*.sls $(DESTDIR)/srv/salt/ceph/start/mds
	install -m 644 srv/salt/ceph/start/mgr/*.sls $(DESTDIR)/srv/salt/ceph/start/mgr
	install -m 644 srv/salt/ceph/start/mon/*.sls $(DESTDIR)/srv/salt/ceph/start/mon
	install -m 644 srv/salt/ceph/start/rgw/*.sls $(DESTDIR)/srv/salt/ceph/start/rgw
	install -m 644 srv/salt/ceph/start/storage/*.sls $(DESTDIR)/srv/salt/ceph/start/storage
	# state files - terminate
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/terminate
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/terminate/ganesha
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/terminate/igw
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/terminate/mds
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/terminate/mgr
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/terminate/mon
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/terminate/rgw
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/terminate/storage
	install -m 644 srv/salt/ceph/terminate/ganesha/*.sls $(DESTDIR)/srv/salt/ceph/terminate/ganesha
	install -m 644 srv/salt/ceph/terminate/igw/*.sls $(DESTDIR)/srv/salt/ceph/terminate/igw
	install -m 644 srv/salt/ceph/terminate/mds/*.sls $(DESTDIR)/srv/salt/ceph/terminate/mds
	install -m 644 srv/salt/ceph/terminate/mgr/*.sls $(DESTDIR)/srv/salt/ceph/terminate/mgr
	install -m 644 srv/salt/ceph/terminate/mon/*.sls $(DESTDIR)/srv/salt/ceph/terminate/mon
	install -m 644 srv/salt/ceph/terminate/rgw/*.sls $(DESTDIR)/srv/salt/ceph/terminate/rgw
	install -m 644 srv/salt/ceph/terminate/storage/*.sls $(DESTDIR)/srv/salt/ceph/terminate/storage
	# state files - tuned
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/tuned
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/tuned/osd
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/tuned/mon
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/tuned/mgr
	install -m 644 srv/salt/ceph/tuned/osd/*.sls $(DESTDIR)/srv/salt/ceph/tuned/osd
	install -m 644 srv/salt/ceph/tuned/mon/*.sls $(DESTDIR)/srv/salt/ceph/tuned/mon
	install -m 644 srv/salt/ceph/tuned/mgr/*.sls $(DESTDIR)/srv/salt/ceph/tuned/mgr
	# conf files - tuned
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/tuned/files
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/tuned/files/ceph-osd
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/tuned/files/ceph-mon
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/tuned/files/ceph-mgr
	install -m 644 srv/salt/ceph/tuned/files/ceph-osd/*.conf $(DESTDIR)/srv/salt/ceph/tuned/files/ceph-osd
	install -m 644 srv/salt/ceph/tuned/files/ceph-mon/*.conf $(DESTDIR)/srv/salt/ceph/tuned/files/ceph-mon
	install -m 644 srv/salt/ceph/tuned/files/ceph-mgr/*.conf $(DESTDIR)/srv/salt/ceph/tuned/files/ceph-mgr
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
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/maintenance/upgrade/report
	install -m 644 srv/salt/ceph/maintenance/upgrade/report/*.sls $(DESTDIR)/srv/salt/ceph/maintenance/upgrade/report
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/maintenance/upgrade/cleanup
	install -m 644 srv/salt/ceph/maintenance/upgrade/cleanup/*.sls $(DESTDIR)/srv/salt/ceph/maintenance/upgrade/cleanup
	# state files - orchestrate stages
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/stage/all
	install -m 644 srv/salt/ceph/stage/all/*.sls $(DESTDIR)/srv/salt/ceph/stage/all/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/stage/cephfs
	install -m 644 srv/salt/ceph/stage/cephfs/*.sls $(DESTDIR)/srv/salt/ceph/stage/cephfs/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/stage/cephfs/core
	install -m 644 srv/salt/ceph/stage/cephfs/core/*.sls $(DESTDIR)/srv/salt/ceph/stage/cephfs/core
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/stage/configure
	install -m 644 srv/salt/ceph/stage/configure/*.sls $(DESTDIR)/srv/salt/ceph/stage/configure/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/stage/deploy
	install -m 644 srv/salt/ceph/stage/deploy/*.sls $(DESTDIR)/srv/salt/ceph/stage/deploy/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/stage/deploy/core
	install -m 644 srv/salt/ceph/stage/deploy/core/*.sls $(DESTDIR)/srv/salt/ceph/stage/deploy/core
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/stage/discovery
	install -m 644 srv/salt/ceph/stage/discovery/*.sls $(DESTDIR)/srv/salt/ceph/stage/discovery/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/stage/ganesha
	install -m 644 srv/salt/ceph/stage/ganesha/*.sls $(DESTDIR)/srv/salt/ceph/stage/ganesha/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/stage/ganesha/core
	install -m 644 srv/salt/ceph/stage/ganesha/core/*.sls $(DESTDIR)/srv/salt/ceph/stage/ganesha/core
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/stage/iscsi
	install -m 644 srv/salt/ceph/stage/iscsi/*.sls $(DESTDIR)/srv/salt/ceph/stage/iscsi/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/stage/iscsi/core
	install -m 644 srv/salt/ceph/stage/iscsi/core/*.sls $(DESTDIR)/srv/salt/ceph/stage/iscsi/core
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
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/stage/radosgw/core
	install -m 644 srv/salt/ceph/stage/radosgw/core/*.sls $(DESTDIR)/srv/salt/ceph/stage/radosgw/core
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/stage/services
	install -m 644 srv/salt/ceph/stage/services/*.sls $(DESTDIR)/srv/salt/ceph/stage/services/
	# state files - orchestrate shared
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/stage/validate
	install -m 644 srv/salt/ceph/stage/validate/*.sls $(DESTDIR)/srv/salt/ceph/stage/validate/
	# state files - sync
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/sync
	install -m 644 srv/salt/ceph/sync/*.sls $(DESTDIR)/srv/salt/ceph/sync/
	# state files - subvolume
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/subvolume
	install -m 644 srv/salt/ceph/subvolume/*.sls $(DESTDIR)/srv/salt/ceph/subvolume/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/setosdflags
	install -m 644 srv/salt/ceph/setosdflags/*.sls $(DESTDIR)/srv/salt/ceph/setosdflags
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/setosdflags/requireosdrelease
	install -m 644 srv/salt/ceph/setosdflags/requireosdrelease/*.sls $(DESTDIR)/srv/salt/ceph/setosdflags/requireosdrelease
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/setosdflags/sortbitwise
	install -m 644 srv/salt/ceph/setosdflags/sortbitwise/*.sls $(DESTDIR)/srv/salt/ceph/setosdflags/sortbitwise
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/time
	install -m 644 srv/salt/ceph/time/default.sls $(DESTDIR)/srv/salt/ceph/time/
	install -m 644 srv/salt/ceph/time/disabled.sls $(DESTDIR)/srv/salt/ceph/time/
	install -m 644 srv/salt/ceph/time/init.sls $(DESTDIR)/srv/salt/ceph/time/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/time/chrony
	install -m 644 srv/salt/ceph/time/chrony/*.sls $(DESTDIR)/srv/salt/ceph/time/chrony/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/time/chrony/files
	install -m 644 srv/salt/ceph/time/chrony/files/*.j2 $(DESTDIR)/srv/salt/ceph/time/chrony/files
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/time/ntp
	install -m 644 srv/salt/ceph/time/ntp/*.sls $(DESTDIR)/srv/salt/ceph/time/ntp/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/time/ntp/files
	install -m 644 srv/salt/ceph/time/ntp/files/*.j2 $(DESTDIR)/srv/salt/ceph/time/ntp/files
	# state files - wait
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/wait
	install -m 644 srv/salt/ceph/wait/*.sls $(DESTDIR)/srv/salt/ceph/wait/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/wait/mds
	install -m 644 srv/salt/ceph/wait/mds/*.sls $(DESTDIR)/srv/salt/ceph/wait/mds/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/wait/1hour/until/OK
	install -m 644 srv/salt/ceph/wait/1hour/until/OK/*.sls $(DESTDIR)/srv/salt/ceph/wait/1hour/until/OK
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/wait/2hours/until/OK
	install -m 644 srv/salt/ceph/wait/2hours/until/OK/*.sls $(DESTDIR)/srv/salt/ceph/wait/2hours/until/OK
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/wait/4hours/until/OK
	install -m 644 srv/salt/ceph/wait/4hours/until/OK/*.sls $(DESTDIR)/srv/salt/ceph/wait/4hours/until/OK
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/wait/until/OK
	install -m 644 srv/salt/ceph/wait/until/OK/*.sls $(DESTDIR)/srv/salt/ceph/wait/until/OK
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/wait/until/expired/30sec
	install -m 644 srv/salt/ceph/wait/until/expired/30sec/*.sls $(DESTDIR)/srv/salt/ceph/wait/until/expired/30sec
	# state files - check processes
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/processes
	install -m 644 srv/salt/ceph/processes/*.sls $(DESTDIR)/srv/salt/ceph/processes/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/processes/admin
	install -m 644 srv/salt/ceph/processes/admin/*.sls $(DESTDIR)/srv/salt/ceph/processes/admin
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/processes/rgw
	install -m 644 srv/salt/ceph/processes/rgw/*.sls $(DESTDIR)/srv/salt/ceph/processes/rgw
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/processes/osd
	install -m 644 srv/salt/ceph/processes/osd/*.sls $(DESTDIR)/srv/salt/ceph/processes/osd
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/processes/mon
	install -m 644 srv/salt/ceph/processes/mon/*.sls $(DESTDIR)/srv/salt/ceph/processes/mon
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/processes/mgr
	install -m 644 srv/salt/ceph/processes/mgr/*.sls $(DESTDIR)/srv/salt/ceph/processes/mgr
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/processes/mds
	install -m 644 srv/salt/ceph/processes/mds/*.sls $(DESTDIR)/srv/salt/ceph/processes/mds
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/processes/ganesha
	install -m 644 srv/salt/ceph/processes/ganesha/*.sls $(DESTDIR)/srv/salt/ceph/processes/ganesha
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/processes/igw
	install -m 644 srv/salt/ceph/processes/igw/*.sls $(DESTDIR)/srv/salt/ceph/processes/igw
	# state files - warning
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/warning
	install -m 644 srv/salt/ceph/warning/*.sls $(DESTDIR)/srv/salt/ceph/warning/
	# state files - warning/noout
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/warning/noout
	install -m 644 srv/salt/ceph/warning/noout/*.sls $(DESTDIR)/srv/salt/ceph/warning/noout/
	# state files - salt
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/salt
	install -m 644 srv/salt/ceph/salt/*.sls $(DESTDIR)/srv/salt/ceph/salt/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/salt/crc
	install -m 644 srv/salt/ceph/salt/crc/*.conf $(DESTDIR)/srv/salt/ceph/salt/crc/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/salt/crc/minion
	install -m 644 srv/salt/ceph/salt/crc/minion/*.sls $(DESTDIR)/srv/salt/ceph/salt/crc/minion/
	install -d -m 755 $(DESTDIR)/srv/salt/ceph/salt/crc/master
	install -m 644 srv/salt/ceph/salt/crc/master/*.sls $(DESTDIR)/srv/salt/ceph/salt/crc/master/

	# state files - orchestrate stage symlinks
	ln -sf prep		$(DESTDIR)/srv/salt/ceph/stage/0
	ln -sf discovery	$(DESTDIR)/srv/salt/ceph/stage/1
	ln -sf configure	$(DESTDIR)/srv/salt/ceph/stage/2
	ln -sf deploy		$(DESTDIR)/srv/salt/ceph/stage/3
	ln -sf services		$(DESTDIR)/srv/salt/ceph/stage/4
	ln -sf removal		$(DESTDIR)/srv/salt/ceph/stage/5

	# cache directories
	install -d -m 700 $(DESTDIR)/srv/salt/ceph/admin/cache
	install -d -m 700 $(DESTDIR)/srv/salt/ceph/ganesha/cache
	install -d -m 700 $(DESTDIR)/srv/salt/ceph/igw/cache
	install -d -m 700 $(DESTDIR)/srv/salt/ceph/mds/cache
	install -d -m 700 $(DESTDIR)/srv/salt/ceph/mgr/cache
	install -d -m 700 $(DESTDIR)/srv/salt/ceph/mon/cache
	install -d -m 700 $(DESTDIR)/srv/salt/ceph/openstack/cache
	install -d -m 700 $(DESTDIR)/srv/salt/ceph/osd/cache
	install -d -m 700 $(DESTDIR)/srv/salt/ceph/rgw/cache
	install -d -m 700 $(DESTDIR)/srv/salt/ceph/configuration/files/ceph.conf.checksum
	# At runtime, these need to be owned by salt:salt.  This won't work
	# in a buildroot on OBS, hence the leading '-' to ignore failures
	# and '|| true' to suppress some error output, but will work fine
	# in development when root runs `make install`.

	-chown $(USER):$(GROUP) $(DESTDIR)/srv/salt/ceph/admin/cache || true
	-chown $(USER):$(GROUP) $(DESTDIR)/srv/salt/ceph/ganesha/cache || true
	-chown $(USER):$(GROUP) $(DESTDIR)/srv/salt/ceph/igw/cache || true
	-chown $(USER):$(GROUP) $(DESTDIR)/srv/salt/ceph/mds/cache || true
	-chown $(USER):$(GROUP) $(DESTDIR)/srv/salt/ceph/mgr/cache || true
	-chown $(USER):$(GROUP) $(DESTDIR)/srv/salt/ceph/mon/cache || true
	-chown $(USER):$(GROUP) $(DESTDIR)/srv/salt/ceph/openstack/cache || true
	-chown $(USER):$(GROUP) $(DESTDIR)/srv/salt/ceph/osd/cache || true
	-chown $(USER):$(GROUP) $(DESTDIR)/srv/salt/ceph/rgw/cache || true
	-chown $(USER):$(GROUP) $(DESTDIR)/srv/salt/ceph/configuration/files/ceph.conf.checksum || true

install-deps:
	# Using '|| true' to suppress failure (packages already installed, etc)
	$(PKG_INSTALL) $(DEEPSEA_DEPS) || true
	$(PKG_INSTALL) $(PYTHON_DEPS) || true

install: pyc install-deps copy-files
	sed -i '/^sharedsecret: /s!{{ shared_secret }}!'`cat /proc/sys/kernel/random/uuid`'!' $(DESTDIR)/etc/salt/master.d/sharedsecret.conf
	chown $(USER):$(GROUP) $(DESTDIR)/etc/salt/master.d/*
	echo "deepsea_minions: '*'" > $(DESTDIR)/srv/pillar/ceph/deepsea_minions.sls
	chown -R $(USER) $(DESTDIR)/srv/pillar/ceph
	# Use '|| true' to suppress some error output in corner cases
	systemctl restart salt-master
	systemctl restart salt-api
	# deepsea-cli
	$(PYTHON) setup.py install --root=$(DESTDIR)/

rpm: tarball
	sed '/^Version:/s/[^ ]*$$/'$(VERSION)'/' deepsea.spec.in > deepsea.spec
	rpmbuild -bb deepsea.spec

# Removing test dependency until resolved
tarball:
	$(eval TEMPDIR := $(shell mktemp -d))
	mkdir $(TEMPDIR)/deepsea-$(VERSION)
	git archive HEAD | tar -x -C $(TEMPDIR)/deepsea-$(VERSION)
	sed "s/DEVVERSION/"$(VERSION)"/" $(TEMPDIR)/deepsea-$(VERSION)/setup.py.in > $(TEMPDIR)/deepsea-$(VERSION)/setup.py
	sed "s/DEVVERSION/"$(VERSION)"/" $(TEMPDIR)/deepsea-$(VERSION)/deepsea.spec.in > $(TEMPDIR)/deepsea-$(VERSION)/deepsea.spec
	sed -i "s/DEVVERSION/"$(VERSION)"/" $(TEMPDIR)/deepsea-$(VERSION)/srv/modules/runners/deepsea.py
	mkdir -p ~/rpmbuild/SOURCES
	cp $(TEMPDIR)/deepsea-$(VERSION)/setup.py .
	tar -cjf ~/rpmbuild/SOURCES/deepsea-$(VERSION).tar.bz2 -C $(TEMPDIR) .
	rm -r $(TEMPDIR)

test: setup.py
	tox -e py3

lint: setup.py
	tox -e lint
