
{% if 'master' not in salt['pillar.get']('roles') and
      'rgw' not in salt['pillar.get']('roles') %}

stop ceph-radosgw:
  cmd.run:
    - name: 'systemctl stop ceph-radosgw@rgw*'
    - onlyif: "test -f /usr/bin/radosgw"

# Need conditional check if all rgw configurations are unassigned
uninstall ceph-radosgw:
  pkg.removed:
    - name: ceph-radosgw

{% endif %}

include:
{% if 'master' not in salt['pillar.get']('roles') and
      'rgw' not in salt['pillar.get']('roles') %}
  - .keyring
{% endif %}
  - .monitoring
