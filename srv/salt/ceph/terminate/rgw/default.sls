
{% for role in salt['rgw.configurations']() %}

stop ceph-radosgw for {{ role }}:
  cmd.run:
    - name: 'systemctl stop ceph-radosgw@{{ role + "." + grains['host'] }}'
    - onlyif: "test -f /usr/bin/radosgw"

{% endfor %}


