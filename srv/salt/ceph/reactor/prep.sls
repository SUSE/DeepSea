
{% if salt['saltutil.runner']('filequeue.add', name='begin', queue='master', duplicate_fail='True') == True %}
master:
  runner.state.orchestrate:
    - mods: ceph.stage.master

{% endif %}

{% if salt['saltutil.runner']('filequeue.check', name='complete', queue='master') == True %}
ceph.prep:
  local.state.apply:
    - tgt: {{ data['id'] }}

{% endif %}

