
include:
  - .install
  - .profiles

"aa-disable /etc/apparmor.d/usr.bin.ceph-mds || true":
  cmd.run

"aa-disable /etc/apparmor.d/usr.bin.ceph-mgr || true":
  cmd.run

"aa-disable /etc/apparmor.d/usr.bin.ceph-mon || true":
  cmd.run

"aa-disable /etc/apparmor.d/usr.bin.ceph-osd || true":
  cmd.run

"aa-disable /etc/apparmor.d/usr.bin.radosgw || true":
  cmd.run
