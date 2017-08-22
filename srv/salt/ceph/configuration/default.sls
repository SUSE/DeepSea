

/etc/ceph/ceph.conf:
  file:
    - managed
    - source:
        - salt://ceph/configuration/cache/ceph.conf
    - template: jinja
    - user: root
    - group: root
    - mode: 644
    - makedirs: True
    - fire_event: True




