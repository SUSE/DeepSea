
{% for role in salt['rgw.configurations']() %}

start ceph-radosgw for {{ role }}:
  cmd.run:
    - name: 'systemctl start ceph-radosgw@{{ role + "." + grains['host'] }}'
    - onlyif: "test -f /usr/bin/radosgw"

{% endfor %}


