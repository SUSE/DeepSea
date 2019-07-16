{% set name = salt['mds.get_name'](grains['host']) %}
restart:
  cmd.run:
    - name: "systemctl restart ceph-mds@{{ name }}.service"
    - unless: "systemctl is-failed ceph-mds@{{ name }}.service"
    - fire_event: True
