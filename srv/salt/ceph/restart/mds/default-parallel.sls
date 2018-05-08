{% set fs_name = salt['saltutil.runner']('cmd.run', cmd='ceph fs dump --format=json-pretty 2>/dev/null | jq --raw-output .filesystems[0].mdsmap.fs_name') %}
{% set ranks_in = salt['saltutil.runner']('cmd.run', cmd='ceph fs dump --format=json-pretty 2>/dev/null | jq ".filesystems[0].mdsmap.in | length"') %}
{% set master = salt['pillar.get']('master_minion') %}

wait till ceph is healthy:
  salt.state:
    - tgt: {{ master }}
    - sls: ceph.wait
    - failhard: True

shrink mds cluster:
  salt.state:
    - tgt: {{ master }}
    - tgt_type: compound
    - sls:
      - ceph.restart.mds.shrink-mds-cluster
    - pillar:
        'fs_name': {{ fs_name }}
        'ranks_in': {{ ranks_in }}

wait until all active mds but one have stopped:
  salt.state:
    - tgt: {{ master }}
    - sls: ceph.wait.mds

{% set standbys = salt['saltutil.runner']('cmd.run', cmd='ceph --format=json fs dump 2>/dev/null | jq -c [.standbys[].name]') | load_json %}
{% for standby in standbys %}
shutdown standby daemon {{ standby }}:
  salt.state:
    - tgt: {{ standby }}
    - sls: ceph.mds.shutdown
{% endfor %}

{% set active = salt['saltutil.runner']('cmd.run', cmd='ceph --format=json fs dump 2>/dev/null | jq --raw-output "[.filesystems[0].mdsmap.info|.[].name] | .[0]"') %}
restarting remaing active {{ active }}:
  salt.state:
    - tgt: '{{ active }}'
    - sls: ceph.mds.restart
    - failhard: True

wait until all active mds are up and active:
  salt.state:
    - tgt: {{ master }}
    - sls: ceph.wait.mds

{% for standby in standbys %}
start standby daemon {{ standby }}:
   salt.state:
     - tgt: {{ standby }}
     - sls: ceph.mds
{% endfor %}

reset mds cluster:
  salt.state:
    - tgt: {{ master }}
    - tgt_type: compound
    - sls:
      - ceph.restart.mds.reset-mds-cluster
    - pillar:
        'fs_name': {{ fs_name }}
        'ranks_in': {{ ranks_in }}

check if all processes are still running after restarting mdss:
  salt.state:
    - tgt: '{{ salt['pillar.get']('deepsea_minions') }}'
    - tgt_type: compound
    - sls: ceph.processes
    - failhard: True

final wait until all active mds are up and active:
  salt.state:
    - tgt: {{ master }}
    - sls: ceph.wait.mds
