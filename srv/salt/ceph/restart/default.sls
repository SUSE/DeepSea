{% if salt['saltutil.runner']('cephprocesses.mon') == True %}
include:
  - .mon
  - .mgr
  - .osd
  - .rgw
  - .mds
  - .igw
  - .ganesha
  - .grafana
  - .prometheus
{% else %}

No Ceph cluster:
  test.nop
{% endif %}
