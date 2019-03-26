{% if salt['cephprocesses.need_restart'](role='igw') == True %}

restart igw gateway {{ grains['host'] }}:
  module.run:
    - name: service.restart
    - m_name: rbd-target-api

unset igw restart grain:
  module.run:
    - name: grains.setval
    - key: restart_igw
    - val: False


{% else %}

igwrestart.noop:
  test.nop

{% endif %}
