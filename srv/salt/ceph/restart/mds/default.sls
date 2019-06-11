
{% if salt.saltutil.runner('cephprocesses.need_restart_config_change', role='mds') %}

include:
  - .default-sequential

{% elif salt.saltutil.runner('cephprocesses.need_restart_lsof', role='mds') %}

{% if salt['saltutil.runner']('cmd.run', cmd='ceph fs dump --format=json-pretty 2>/dev/null | jq --raw-output ".filesystems | length"') == "0" %}

{# we have mds daemons but no fs, simply restart everything #}
restart all mds daemons:
  salt.state:
    - tgt: 'I@roles:mds'
    - tgt_type: compound
    - sls: ceph.mds.restart
    - failhard: True

{% else %}

include:
  - .default-shrink

{% endif %}

{% else %}

mds restart noop:
  test.nop

{% endif %}
