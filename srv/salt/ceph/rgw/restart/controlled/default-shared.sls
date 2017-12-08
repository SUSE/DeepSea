{% for role in salt['pillar.get']('rgw_configurations', [ 'rgw' ]) %}
    restart:
      cmd.run:
        - name: "systemctl restart ceph-radosgw@{{ role }}.service"
        - unless: "systemctl is-failed ceph-radosgw@{{ role }}.service"
        - fire_event: True
{% endfor %}

