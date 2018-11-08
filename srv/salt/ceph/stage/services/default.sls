{% set master = salt['master.minion']() %} 

{% if salt['saltutil.runner']('validate.deploy', cluster='ceph') == False %}

validate failed:
  salt.state:
    - name: just.exit
    - tgt: {{ master }}
    - failhard: True

{% endif %}

include:
  - ..iscsi
  - ..cephfs
  - ..radosgw
  - ..ganesha
