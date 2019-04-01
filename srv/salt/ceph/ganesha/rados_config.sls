{% for host in salt.saltutil.runner('select.minions', cluster='ceph', roles='ganesha', host=True) %}

create {{ host }} daemon rados object:
  cmd.run:
    - name: "POOL=`salt-call --out=json deepsea.find_pool '[\"cephfs\", \"rgw\"]' 2>/dev/null | jq -r .local` && rados -p $POOL -N ganesha create conf-{{ host }}"
    - unless: "POOL=`salt-call --out=json deepsea.find_pool '[\"cephfs\", \"rgw\"]' 2>/dev/null | jq -r .local` && rados -p $POOL -N ganesha ls | grep -q ^conf-{{ host }}$"
    - fire_event: True

{% endfor %}