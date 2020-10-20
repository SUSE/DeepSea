
{% for i in range(salt['pillar.get']('mds_daemons_per_node', 1)) %}

{% set name = salt['mds.get_name'](grains['host'], i) %}
/var/lib/ceph/mds/ceph-{{ name }}/keyring:
  file.absent

{% endfor %}

/var/lib/ceph/mds/ceph-mds/keyring:
  file.absent

