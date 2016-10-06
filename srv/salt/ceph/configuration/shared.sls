

/etc/ceph/ceph.conf:
  file:
    - managed
    - source:
        - salt://ceph/configuration/files/ceph.conf-shared.j2
    - template: jinja
    - user: root
    - group: root
    - mode: 644
    - makedirs: True
    - fire_event: True




