{% set fs_name = salt['pillar.get']('fs_name') %}
{% set ranks_in = salt['pillar.get']('ranks_in') %}

{% if fs_name == "" or ranks_in == "" %}

no file system name or rank target supplied:
  test.fail_without_changes:
    - name: |
        Please specify both fs_name and ranks_in pillar vars:
        salt <target> state.apply ceph.mds.restart.shrink-mds-cluster \
        pillar='{"fs_name": "<name>", "ranks_in": "<target_ranks>"}'

{% else %}

set max_mds back to {{ ranks_in }}:
  cmd.run:
    - failhard: True
    - name: ceph fs set {{ fs_name }} max_mds {{ ranks_in }}

{% endif %}
