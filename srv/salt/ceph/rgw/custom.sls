
include:
  - .keyring

install rgw:
  cmd.run:
    - name: "zypper --non-interactive --no-gpg-checks in ceph-radosgw"


{% for role in salt['pillar.get']('rgw_configurations', [ 'rgw' ]) %}
start {{ role }}:
  service.running:
    - name: ceph-radosgw@{{ role + "." + grains['host'] }}
    - enable: True
    - require:
        - cmd: install rgw
{% endfor %}

