
remove openattic nop:
  test.nop

{% if salt.saltutil.runner('select.minions', cluster='ceph', roles='openattic') == [] %}

remove openattic auth:
  cmd.run:
    - name: "ceph auth del client.openattic"

{% endif %}

/var/cache/salt/master/jobs:
  file.directory:
    - user: {{ salt['deepsea.user']() }}
    - group: {{ salt['deepsea.group']() }}
    - recurse:
      - user
      - group

