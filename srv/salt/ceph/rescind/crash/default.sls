
crash nop:
  test.nop

{% if not salt['pillar.get']('roles') %}
/etc/ceph/ceph.client.crash.keyring:
  file.absent
{% endif %}
