
remove openattic nop:
  test.nop

{% if salt.saltutil.runner('select.minions', cluster='ceph', roles='openattic') == [] %}

remove openattic auth:
  cmd.run:
    - name: "ceph auth del client.openattic"

{% endif %}
