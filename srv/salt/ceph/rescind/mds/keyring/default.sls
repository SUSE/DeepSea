
{% set name = salt['mds.get_name'](grains['host']) %}
/var/lib/ceph/mds/ceph-{{ name }}/keyring:
  file.absent

/var/lib/ceph/mds/ceph-mds/keyring:
  file.absent


