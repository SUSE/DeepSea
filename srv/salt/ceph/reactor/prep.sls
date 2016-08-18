

{% if salt['saltutil.runner']('filequeue.check', name='complete', queue='master') == True %}
ceph.prep:
  local.state.apply:
    - tgt: {{ data['id'] }}

{% endif %}

