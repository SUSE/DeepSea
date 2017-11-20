{% if salt['cephprocesses.need_restart'](role='ganesha') == True %}

restart nfs-ganesha:
  module.run:
    - name: service.restart
    - m_name: nfs-ganesha

unset ganesha restart grain:
  module.run:
    - name: grains.setval
    - key: restart_ganesha
    - val: False


{% else %}

ganesharestart.noop:
  test.nop

{% endif %}
