

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

