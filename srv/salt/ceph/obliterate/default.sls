
storage nop:
  test.nop

{% for id in salt['osd.list']() %}

removing {{ id }}:
  module.run:
    - name: osd.remove
    - osd_id: {{ id }}
    - kwargs:
        force: True

{% endfor %}

