
include:
  - .keyring

install rgw:
  pkg.installed:
    - name: ceph-radosgw

{% for role in salt['rgw.configurations']() %}

start {{ role }}:
  service.running:
    - name: ceph-radosgw@{{ role + "." + grains['host'] }}
    - enable: True

{% endfor %}

