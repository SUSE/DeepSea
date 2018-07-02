{% if salt['saltutil.runner']('cephprocesses.mon') == True %}
include:
  - .mon
  - .mgr
  - .osd
  - .rgw
  - .mds
  - .igw
  - .ganesha
# disabled due to https://github.com/SUSE/DeepSea/issues/816
#  - .openattic 
{% else %}

No Ceph cluster:
  test.nop
{% endif %}

