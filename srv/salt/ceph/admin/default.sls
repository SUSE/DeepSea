
/etc/ceph/ceph.client.admin.keyring:
  file.managed:
    - source: 
      - salt://ceph/admin/cache/ceph.client.admin.keyring
    - user: root
    - group: root
    - mode: 600

