{% if salt['cephprocesses.need_restart'](role='storage') == True %}
{% set osd_list = salt['osd.list']() %}
{% for id in osd_list %}
restart osd {{ id }}:
  cmd.run:
    - name: "systemctl restart ceph-osd@{{ id }}.service"
    - unless: "systemctl is-failed ceph-osd@{{ id }}.service"
    - fire_event: True
    - failhard: True

wait on processes after processing osd.{{ id }}:
  module.run:
    - name: cephprocesses.wait
    - kwargs:
        'roles': ["storage"]
    - fire_event: True
    - failhard: True
{% endfor %}

{% for id in osd_list %}
ensure osd.{{ id }} is active:
  module.run:
    - name: osd.wait_until_available
    - osd_id: {{ id }}
    - failhard: True
{% endfor %}

unset storage restart grain:
  module.run:
    - name: grains.setval
    - key: restart_storage
    - val: False

{% else %}

osdrestart.noop:
  test.nop

{% endif %}
