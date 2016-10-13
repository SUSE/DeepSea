
remove mon nop:
  test.nop

{% for minion in salt['mon.list']() %}
{% if minion not in salt['pillar.get']('mon_initial_members') %}
remove mon.{{ minion }}:
  cmd.run:
    - name: "ceph mon remove {{ minion }} || :"
{% endif %}
{% endfor %}

