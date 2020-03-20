
{% for i in range(salt['pillar.get']('mds_daemons_per_node', 1)) %}

{% set name = salt['mds.get_name'](grains['host'], i) %}

restart {{ name }}:
  cmd.run:
    - name: "systemctl restart ceph-mds@{{ name }}.service"
    - unless: "systemctl is-failed ceph-mds@{{ name }}.service"
    - fire_event: True
{% endfor %}
