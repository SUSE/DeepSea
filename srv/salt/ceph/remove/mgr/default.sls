
remove mgr nop:
  test.nop

{% if salt.saltutil.runner('select.minions', cluster='ceph', roles='mgr') == [] %}

remove mgr auth:
  cmd.run:
    - name: "for id in $(ceph auth list 2>/dev/null | grep '^mgr\\.') ; do ceph auth del $id ; done"


{% endif %}

/var/cache/salt/master/jobs:
  file.directory:
    - user: {{ salt['deepsea.user']() }}
    - group: {{ salt['deepsea.group']() }}
    - recurse:
      - user
      - group

