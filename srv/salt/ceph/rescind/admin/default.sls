
admin nop:
  test.nop

{% if 'master' not in salt['pillar.get']('roles') and 
      'admin' not in salt['pillar.get']('roles') %}
/etc/ceph/ceph.client.admin.keyring:
  file.absent
{% endif %}
