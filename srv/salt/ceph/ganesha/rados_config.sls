{% for host in salt.saltutil.runner('select.minions', cluster='ceph', roles='ganesha', host=True) %}

create {{ host }} daemon rados object:
  cmd.run:
    - name: "rados -p ganesha_config -N ganesha create conf-{{ host }}"
    - unless: "rados -p $POOL -N ganesha ls | grep -q ^conf-{{ host }}$"
    - fire_event: True

{% endfor %}
