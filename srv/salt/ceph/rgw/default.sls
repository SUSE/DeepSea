{% set rgw_name = salt['pillar.get']('rgw_service_name', 'rgw')  %}
{% set rgw_instance = salt['grains.get']('id').split('.')[0] %}
install rgw:
  pkg.installed:
    - name: ceph-radosgw

start rgw:
  service.running:
    - name: ceph-radosgw@{{ rgw_name }}.{{ rgw_instance }}
    - enable: True
    - require:
        - pkg: install rgw
