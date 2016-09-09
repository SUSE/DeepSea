{% set rgw_name = salt['pillar.get']('rgw_service_name', 'rgw')  %}
install rgw:
  pkg.install:
    - name: ceph-radosgw

start rgw:
  service.running:
    - name: ceph-radosgw@{{ rgw_name }}.{{ grains['host'] }}
    - enable: True
    - require:
        - pkg: install rgw
