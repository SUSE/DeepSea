
/usr/lib/systemd/system/ceph-mon@.service:
  file.managed:
    - source:
      - salt://ceph/mon/files/ceph-mon.service.j2
    - template: jinja
    - user: root
    - group: root
    - mode: 600
    - makedirs: True
    - fire_event: True
