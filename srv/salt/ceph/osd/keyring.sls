
/var/lib/ceph/bootstrap-osd/ceph.keyring:
  file.managed:
    - source:
      - salt://ceph/osd/files/keyring.j2
    - template: jinja
    - user: root
    - group: root
    - mode: 600
    - makedirs: True
    - fire_event: True


