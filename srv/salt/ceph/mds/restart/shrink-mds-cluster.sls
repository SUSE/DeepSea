{% set fs_name = salt['pillar.get']('fs_name') %}
{% set ranks_in = salt['pillar.get']('ranks_in') %}

set max_mds to 1:
  cmd.run:
    - name: ceph fs set {{ fs_name }} max_mds 1
    - failhard: True

{% for rank in range(1, ranks_in|int)|reverse %}

deactivate mds rank {{ rank }}:
  cmd.run:
    - name: ceph mds deactivate {{ fs_name }}:{{ rank }}
    - failhard: True

{% endfor %}
