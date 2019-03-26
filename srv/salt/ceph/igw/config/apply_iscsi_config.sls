/etc/ceph/iscsi-gateway.cfg:
  file.managed:
    - source: 
      - salt://ceph/igw/cache/iscsi-gateway.{{ grains['host'] }}.cfg
    - user: root
    - group: root
    - mode: 600
    - fire_event: True
