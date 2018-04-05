{% set fs_name = salt['pillar.get']('fs_name') %}
{% set ranks_in = salt['pillar.get']('ranks_in') %}

set max_mds back to {{ ranks_in }}:
  cmd.run:
    - failhard: True
    - name: ceph fs set {{ fs_name }} max_mds {{ ranks_in }}

