/etc/ceph/iscsi-gateway.cfg:
  file.managed:
    - source:
      - salt://ceph/igw/cache/iscsi-gateway.{{ grains['host'] }}.cfg
    - user: root
    - group: root
    - mode: 600
    - fire_event: True

{% if pillar.get('ceph_iscsi_ssl', True) %}

/etc/ceph/iscsi-gateway.crt:
  file.managed:
    - source:
      - salt://ceph/igw/cache/tls/certs/iscsi-gateway.crt
    - user: root
    - group: root
    - mode: 600
    - fire_event: True

/etc/ceph/iscsi-gateway.key:
  file.managed:
    - source:
      - salt://ceph/igw/cache/tls/certs/iscsi-gateway.key
    - user: root
    - group: root
    - mode: 600
    - fire_event: True

{% endif %}
