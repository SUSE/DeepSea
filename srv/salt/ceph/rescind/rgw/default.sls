
rgw nop:
  test.nop

/srv/salt/ceph/rgw/cache/:
    file.absent

{% if 'rgw' not in salt['pillar.get']('roles') %}
stop ceph-radosgw:
  service.dead:
    - name: ceph-radosgw@rgw.*
    - enable: False
    - onlyif: "test -f /usr/bin/radosgw"

# Need conditional check if all rgw configurations are unassigned
uninstall ceph-radosgw:
  pkg.removed:
    - name: ceph-radosgw

include:
- .keyring
{% endif %}
