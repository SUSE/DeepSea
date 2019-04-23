clean up node_exporter cache dir:
  file.absent:
    - name: /srv/salt/ceph/monitoring/prometheus/cache/node_exporter

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

clean up prometheus cache dir:
  file.absent:
    - name: /srv/salt/ceph/monitoring/prometheus/cache/prometheus

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

clean up alertmanager cache dir:
  file.absent:
    - name: /srv/salt/ceph/monitoring/prometheus/cache/alertmanager

{% for minion in salt.saltutil.runner('select.minions', cluster='ceph', host=False, roles='prometheus') %}
/srv/salt/ceph/monitoring/prometheus/cache/alertmanager/{{ minion }}.yml:
  file.managed:
    - user: {{ salt['deepsea.user']() }}
    - group: {{ salt['deepsea.group']() }}
    - mode: 600
    - makedirs: True
    - fire_event: True
    - source: salt://ceph/monitoring/prometheus/files/minion.yml.j2
    - template: jinja
    - context:
        minion: {{ minion }}:9093
{% endfor %}

clean up grafana cache dir:
  file.absent:
    - name: /srv/salt/ceph/monitoring/prometheus/cache/grafana

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
