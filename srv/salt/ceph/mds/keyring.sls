
/var/lib/ceph/mds/ceph-mds.{{ grains['host'] }}/ceph.keyring:
  file.managed:
    - source:
      - salt://ceph/mds/files/keyring.j2
    - template: jinja
    - user: salt
    - group: salt
    - mode: 600
    - makedirs: True
    - context:
      mds: {{ grains['host'] }}
    - fire_event: True


