
configuration nop:
  test.nop

{% if not salt['pillar.get']('roles') %}
/etc/ceph/ceph.conf:
  file.absent
{% endif %}
