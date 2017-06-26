
/var/lib/ceph/bootstrap-osd/ceph.keyring:
  file.managed:
    - source: salt://ceph/osd/cache/bootstrap.keyring
    - user: root
    - group: root
    - mode: 600

/etc/ceph/ceph.client.storage.keyring:
  file.managed:
    - source: salt://ceph/osd/cache/ceph.client.storage.keyring
    - user: root
    - group: root
    - mode: 600

