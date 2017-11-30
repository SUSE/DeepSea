{% if salt['cephprocesses.need_restart'](role='rgw') == True %}

{% for role in salt['pillar.get']('rgw_configurations', [ 'rgw' ]) %}
restart {{ role }}:
  cmd.run:
    - name: "systemctl restart ceph-radosgw@{{ role + "." + grains['host'] }}.service"
    - unless: "systemctl is-failed ceph-radosgw@{{ role + "." + grains['host'] }}.service"
    - fire_event: True
{% endfor %}

unset rgw restart grain:
  module.run:
    - name: grains.setval
    - key: restart_rgw
    - val: False


{% else %}

rgwrestart.noop:
  test.nop

{% endif %}
