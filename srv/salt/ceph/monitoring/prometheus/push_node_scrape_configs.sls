
{% for minion in salt.saltutil.runner('select.minions', cluster='ceph', host=False) %}
/etc/prometheus/ses/node_{{ minion }}.yml:
  file.managed:
    - user: prometheus
    - group: prometheus
    - mode: 644
    - makedirs: True
    - fire_event: True
    - source: salt://ceph/monitoring/prometheus/cache/{{ minion }}.yml
{% endfor %}
