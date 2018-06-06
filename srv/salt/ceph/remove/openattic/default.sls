
remove openattic nop:
  test.nop

{% if salt.saltutil.runner('select.minions', cluster='ceph', roles='openattic') == [] %}

remove openattic auth:
  cmd.run:
    - name: "ceph auth del client.openattic"

{% endif %}

fix salt job cache permissions:
  cmd.run:
  - name: "find /var/cache/salt/master/jobs -user root -exec chown {{ salt['deepsea.user']() }}:{{ salt['deepsea.group']() }} {} ';'"

