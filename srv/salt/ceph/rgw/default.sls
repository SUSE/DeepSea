
include:
  - .keyring

install rgw:
  pkg.installed:
    - name: ceph-radosgw
    - refresh: True
    - fire_event: True

{% for role in salt['rgw.configurations']() %}

start {{ role }}:
  service.running:
    - name: ceph-radosgw@{{ role + "." + grains['host'] }}
    - enable: True
    - fire_event: True

{% endfor %}

