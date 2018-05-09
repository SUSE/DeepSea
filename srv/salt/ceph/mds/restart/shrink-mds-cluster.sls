{% set fs_name = salt['pillar.get']('fs_name') %}

set max_mds to 1:
  cmd.run:
    - name: ceph fs set {{ fs_name }} max_mds 1
    - failhard: True
