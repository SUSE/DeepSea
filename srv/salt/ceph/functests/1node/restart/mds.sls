
{% set service = 'mds' %}
{% set test_node = salt.saltutil.runner('select.one_minion', cluster='ceph', roles=service) %}

{% include slspath + '/common.sls' %}

{# check shrinking of mds cluster #}

{% set fs_name = salt['saltutil.runner']('cmd.run', cmd='ceph fs dump --format=json-pretty 2>/dev/null | jq --raw-output .filesystems[0].mdsmap.fs_name') %}
{% set ranks_in = salt['saltutil.runner']('cmd.run', cmd='ceph fs dump --format=json-pretty 2>/dev/null | jq ".filesystems[0].mdsmap.in | length"') %}
{% set master = salt['pillar.get']('master_minion') %}

shrink mds cluster:
  salt.state:
    - tgt: {{ master }}
    - tgt_type: compound
    - sls:
      - ceph.mds.restart.shrink-mds-cluster
    - pillar:
        'fs_name': {{ fs_name }}
        'ranks_in': {{ ranks_in }}

wait until all active mds but one have stopped:
  salt.state:
    - tgt: {{ master }}
    - sls: ceph.wait.mds.1-mds

{# check resetting of mds cluster #}

reset mds cluster:
  salt.state:
    - tgt: {{ master }}
    - tgt_type: compound
    - sls:
      - ceph.mds.restart.reset-mds-cluster
    - pillar:
        'fs_name': {{ fs_name }}
        'ranks_in': {{ ranks_in }}

wait until all mds are back:
  salt.state:
    - tgt: {{ master }}
    - sls: ceph.wait.mds

