
{% set service = 'mds' %}
{% set test_node = salt.saltutil.runner('select.one_minion', cluster='ceph', roles=service) %}

{% include slspath + '/common.sls' %}

{# check shrinking of mds cluster #}

{% set fs_name = salt['saltutil.runner']('cmd.run', cmd='ceph fs dump --format=json-pretty 2>/dev/null | jq --raw-output .filesystems[0].mdsmap.fs_name') %}
{% set ranks_in = salt['saltutil.runner']('cmd.run', cmd='ceph fs dump --format=json-pretty 2>/dev/null | jq ".filesystems[0].mdsmap.in | length"') %}
{% set master = salt['master.minion']() %}

shrink mds cluster:
  salt.state:
    - tgt: {{ master }}
    - tgt_type: compound
    - sls:
      - ceph.mds.restart.shrink-mds-cluster
    - pillar:
        'fs_name': {{ fs_name }}

wait until all active mds but one have stopped:
  salt.state:
    - tgt: {{ master }}
    - sls: ceph.wait.mds

{% set after_shrink = salt['saltutil.runner']('cmd.run', cmd='ceph fs dump --format=json-pretty 2>/dev/null | jq ".filesystems[0].mdsmap.in | length"') %}
{% if after_shrink|int ==  %}

mds cluster shrunk:
  test.succeed_without_changes:
    - name: mds cluster shrunk to 1

{% else %}

mds cluster not shrunk:
  test.fail_without_changes:
    - name: mds cluster not shrunk, size {{ after_shrink }}

{% endif %}

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

wait until all active mds but one have stopped:
  salt.state:
    - tgt: {{ master }}
    - sls: ceph.wait.mds

{% set after_reset = salt['saltutil.runner']('cmd.run', cmd='ceph fs dump --format=json-pretty 2>/dev/null | jq ".filesystems[0].mdsmap.in | length"') %}
{% if after_reset == ranks_in %}

mds cluster reset:
  test.succeed_without_changes:
    - name: mds cluster reset to {{ after_reset }}

{% else %}

mds cluster not reset:
  test.fail_without_changes:
    - name: mds cluster not reset

{% endif %}
