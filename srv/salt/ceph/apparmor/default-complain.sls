
include:
  - .install
  - .profiles

aa-complain /etc/apparmor.d/usr.bin.ceph-mds:
  cmd.run

aa-complain /etc/apparmor.d/usr.bin.ceph-mgr:
  cmd.run

aa-complain /etc/apparmor.d/usr.bin.ceph-mon:
  cmd.run

aa-complain /etc/apparmor.d/usr.bin.ceph-osd:
  cmd.run

aa-complain /etc/apparmor.d/usr.bin.radosgw:
  cmd.run

aa-complain /etc/apparmor.d/usr.sbin.httpd-prefork:
  cmd.run

aa-complain /etc/apparmor.d/usr.sbin.oaconfig:
  cmd.run
