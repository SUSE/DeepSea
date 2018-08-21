
remove storage nop:
  test.nop

{% for id in salt.saltutil.runner('rescinded.ids') %}

remove osd.{{ id }}:
  cmd.run:
    - name: "ceph osd crush remove osd.{{ id }}"

delete osd.{{ id }} key:
  cmd.run:
    - name: "ceph auth del osd.{{ id }}"

remove id {{ id }}:
  cmd.run:
    - name: "ceph osd rm {{ id }}"

{% endfor %}

delete orphaned host buckets:
  salt.runner:
    - name: rescinded.delete_orphaned_host_buckets

fix salt job cache permissions:
  cmd.run:
  - name: "find /var/cache/salt/master/jobs -user root -exec chown {{ salt['deepsea.user']() }}:{{ salt['deepsea.group']() }} {} ';'"

