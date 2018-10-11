{% if salt['saltutil.runner']('disengage.check', cluster='ceph') == False %}
safety is engaged:
  salt.state:
    - tgt: {{ salt['master.minion']() }}
    - name: "Run 'salt-run disengage.safety' to disable"
    - failhard: True

{% endif %}

{% if salt['saltutil.runner']('cephprocesses.mon') == True %}
include:
  - ..mon.force
  - ..mgr.force
  - ..osd.force
  - ..rgw.force
  - ..mds.force
  - ..igw.force
  - ..ganesha.force
{% else %}

No Ceph cluster:
  test.nop
{% endif %}

