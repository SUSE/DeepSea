{% set nfs_pool = salt['deepsea.find_pool'](['cephfs', 'rgw']) %}
{% for host in salt.saltutil.runner('select.minions', cluster='ceph', roles='ganesha', host=True) %}

create {{ host }} daemon rados object:
  cmd.run:
    - name: "rados -p {{ nfs_pool }} -N ganesha create conf-{{ host }}"
    - unless: "rados -p {{ nfs_pool }} -N ganesha ls | grep -q ^conf-{{ host }}$"
    - fire_event: True

{% endfor %}