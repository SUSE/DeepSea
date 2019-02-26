clean up cache dir:
  file.absent:
    - name: /srv/salt/ceph/monitoring/prometheus/cache/

{% for minion in salt.saltutil.runner('select.minions', cluster='ceph', host=False) %}
/srv/salt/ceph/monitoring/prometheus/cache/node_exporter/{{ minion }}.yml:
  file.managed:
    - user: {{ salt['deepsea.user']() }}
    - group: {{ salt['deepsea.group']() }}
    - mode: 600
    - makedirs: True
    - fire_event: True
    - source: salt://ceph/monitoring/prometheus/files/minion.yml.j2
    - template: jinja
    - context:
        minion: {{ minion }}:9100
{% endfor %}

{% for minion in salt.saltutil.runner('select.minions', cluster='ceph', host=False, roles='prometheus') %}
/srv/salt/ceph/monitoring/prometheus/cache/prometheus/{{ minion }}.yml:
  file.managed:
    - user: {{ salt['deepsea.user']() }}
    - group: {{ salt['deepsea.group']() }}
    - mode: 600
    - makedirs: True
    - fire_event: True
    - source: salt://ceph/monitoring/prometheus/files/minion.yml.j2
    - template: jinja
    - context:
        minion: {{ minion }}:9090
{% endfor %}

{% for minion in salt.saltutil.runner('select.minions', cluster='ceph', host=False, roles='grafana') %}
/srv/salt/ceph/monitoring/prometheus/cache/grafana/{{ minion }}.yml:
  file.managed:
    - user: {{ salt['deepsea.user']() }}
    - group: {{ salt['deepsea.group']() }}
    - mode: 600
    - makedirs: True
    - fire_event: True
    - source: salt://ceph/monitoring/prometheus/files/minion.yml.j2
    - template: jinja
    - context:
        minion: {{ minion }}:3000
{% endfor %}
