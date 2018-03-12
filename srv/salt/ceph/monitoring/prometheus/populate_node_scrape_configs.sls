{% for minion in salt.saltutil.runner('select.minions', cluster='ceph', host=False) %}
/srv/salt/ceph/monitoring/prometheus/cache/{{ minion }}.yml:
  file.managed:
    - user: {{ salt['deepsea.user']() }}
    - group: {{ salt['deepsea.group']() }}
    - mode: 600
    - makedirs: True
    - fire_event: True
    - source: salt://ceph/monitoring/prometheus/files/minion.yml.j2
    - template: jinja
    - context:
        minion: {{ minion }}
{% endfor %}
