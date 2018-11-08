{% if salt['saltutil.runner']('cephprocesses.mon') == True %}
include:
  - .mon
  - .mgr
  - .osd
  - .rgw
  - .mds
  - .igw
  - .ganesha
{% else %}

No Ceph cluster:
  test.nop
{% endif %}

