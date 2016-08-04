
/etc/ceph/ceph.client.iscsi.keyring:
  file.managed:
    - source: 
      - salt://ceph/iscsi/files/ceph.client.iscsi.keyring
    - user: root
    - group: root
    - mode: 600

