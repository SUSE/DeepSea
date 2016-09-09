{% set rgw_name = salt['pillar.get']('rgw_service_name', 'rgw')  %}
start rgw:
  service.running:
    - name: ceph-rgw@{{ rgw_name }}.{{ grains['host'] }}
    - enable: True
