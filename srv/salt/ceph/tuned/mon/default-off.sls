{% set active_profile = salt['cmd.run']('tuned-adm active') %}

{% if 'No current active profile' not in active_profile %}

stop tuned:
  service.dead:
    - name: tuned
    - enable: False

{% else %}

mon.nop:
  test.nop

{% endif %}
