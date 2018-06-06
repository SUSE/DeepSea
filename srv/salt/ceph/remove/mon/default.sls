
remove mon nop:
  test.nop

{% for minion in salt['mon.list']() %}
{% if minion not in salt.saltutil.runner('select.minions', cluster='ceph', roles='mon', host=True) %}
remove mon.{{ minion }}:
  cmd.run:
    - name: "ceph mon remove {{ minion }} || :"
{% endif %}
{% endfor %}

fix salt job cache permissions:
  cmd.run:
  - name: "find /var/cache/salt/master/jobs -user root -exec chown {{ salt['deepsea.user']() }}:{{ salt['deepsea.group']() }} {} ';'"

