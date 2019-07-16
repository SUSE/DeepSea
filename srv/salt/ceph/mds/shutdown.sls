{% set name = salt['mds.get_name'](grains['host']) %}
shutdown daemon:
  service.dead:
    - name: ceph-mds@{{ name }}
