
{% for i in range(salt['pillar.get']('mds_daemons_per_node', 1)) %}

{% set name = salt['mds.get_name'](grains['host'], i) %}

shutdown daemon {{ name }}:
  service.dead:
    - name: ceph-mds@{{ name }}
{% endfor %}
