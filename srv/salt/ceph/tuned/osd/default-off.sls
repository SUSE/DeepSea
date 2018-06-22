{% set active_profile = salt['cmd.run']('tuned-adm active') %}

{% if 'No current active profile' not in active_profile %}

tuned off:
  tuned.off: []

disable tuned:
  service.disabled:
    - name: tuned

{% else %}

osd.nop:
  test.nop

{% endif %}
