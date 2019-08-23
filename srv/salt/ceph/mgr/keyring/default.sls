/var/lib/ceph/mgr/ceph-{{ grains['host'] }}/keyring:
  file.managed:
    - source:
      - salt://ceph/mgr/cache/{{ grains['host'] }}.keyring
    - template: jinja
    - user: root
    - group: root
    - mode: 600
    - makedirs: True
    - fire_event: True
