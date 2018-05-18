
{% if salt.saltutil.runner('cephprocesses.need_restart_config_change', role='mds') %}

include:
  - .default-sequential

{% elif salt.saltutil.runner('cephprocesses.need_restart_lsof', role='mds') %}

include:
  - .default-shrink

{% else %}

mds restart noop:
  test.nop

{% endif %}
