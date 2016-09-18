
install rgw:
  cmd.run:
    - name: "zypper --non-interactive --no-gpg-checks in ceph-radosgw"


{% for config in salt['pillar.get']('rgw_configurations', [ 'rgw' ]) %}
start {{ config }}:
  service.running:
    - name: ceph-radosgw@{{ config }}
    - enable: True
    - require:
        - cmd: install rgw

{% endfor %}
