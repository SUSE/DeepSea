
/etc/ceph/ceph.client.iscsi.keyring:
  file.managed:
    - source: 
      - salt://ceph/iscsi/files/keyring.j2
    - template: jinja
    - user: root
    - group: root
    - mode: 600

