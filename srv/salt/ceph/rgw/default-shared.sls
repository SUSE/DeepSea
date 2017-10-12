
include:
  - .keyring

install rgw:
  pkg.installed:
    - name: ceph-radosgw
    - refresh: True

{% for role in salt['pillar.get']('rgw_configurations', [ 'rgw' ]) %}
start {{ role }}:
  service.running:
    - name: ceph-radosgw@{{ role }}
    - enable: True

restart {{ role }}:
  module.run:
    - name: service.restart
    - m_name: ceph-radosgw@{{ role }}

{% endfor %}

