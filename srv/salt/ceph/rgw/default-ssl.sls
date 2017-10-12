
# change the init.sls to default-ssl  to use this file
include:
  - .keyring
  - .cert

install rgw:
  pkg.installed:
    - name: ceph-radosgw
    - refresh: True

{% for role in salt['pillar.get']('rgw_configurations', [ 'rgw' ]) %}

start {{ role }}:
  service.running:
    - name: ceph-radosgw@{{ role + "." + grains['host'] }}
    - enable: True

{% endfor %}
