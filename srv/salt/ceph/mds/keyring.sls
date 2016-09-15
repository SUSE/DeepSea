
/var/lib/ceph/mds/ceph-{{ grains['host'] }}/keyring:
  file.managed:
    - source:
      - salt://ceph/mds/files/keyring.j2
    - template: jinja
    - user: ceph
    - group: ceph
    - mode: 600
    - makedirs: True
    - context:
      mds: {{ grains['host'] }}
    - fire_event: True


