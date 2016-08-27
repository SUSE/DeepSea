
# The lock prevents multiple orchestrate runners from running.  For 
# automation, the last stage will remove the lock.  Overlapping restarts
# will trigger only one run.

{% if salt['saltutil.runner']('filequeue.add', name='lock', queue='master', duplicate_fail=True) == True %}

master:
  runner.state.orchestrate:
    - mods: ceph.stage.prep

{% endif %}


# Unfortunately this is a duplicate of /srv/salt/ceph/stage/prep/default.sls
# The difference is these steps are only performed for the restarted minion
# and only if the master has completed its prep stage.

{% if salt['saltutil.runner']('filequeue.check', name='complete', queue='master') == True %}
ceph.sync:
  local.state.apply:
    - tgt: {{ data['id'] }}

ceph.mine_functions:
  local.state.apply:
    - tgt: {{ data['id'] }}

ceph.repo:
  local.state.apply:
    - tgt: {{ data['id'] }}

ceph.updates:
  local.state.apply:
    - tgt: {{ data['id'] }}

{% endif %}

