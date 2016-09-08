
/etc/ceph/ceph.client.admin.keyring:
  file.managed:
    - source: 
      - salt://ceph/admin/files/keyring.j2
    - template: jinja
    - user: ceph
    - group: ceph
    - mode: 600
    - makedirs: True
    - fire_event: True

