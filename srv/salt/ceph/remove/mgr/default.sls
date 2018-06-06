
remove mgr nop:
  test.nop

{% if salt.saltutil.runner('select.minions', cluster='ceph', roles='mgr') == [] %}

remove mgr auth:
  cmd.run:
    - name: "for id in $(ceph auth list 2>/dev/null | grep '^mgr\\.') ; do ceph auth del $id ; done"


{% endif %}

fix salt job cache permissions:
  cmd.run:
  - name: "find /var/cache/salt/master/jobs -user root -exec chown {{ salt['deepsea.user']() }}:{{ salt['deepsea.group']() }} {} ';'"

