

/var/lib/ceph/mgr/ceph-{{ grains['host'] }}/keyring:
  file.managed:
    - source:
      - salt://ceph/mgr/cache/{{ grains['host'] }}.keyring
    - template: jinja
    - user: ceph
    - group: ceph
    - mode: 600
    - makedirs: True
    - fire_event: True

