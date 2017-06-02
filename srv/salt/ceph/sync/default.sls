
load modules:
  module.run:
    - name: saltutil.sync_all
    - refresh: True
    - fire_event: True

{% for minion in salt.saltutil.runner('select.minions', cluster='ceph', host=False) %}
/etc/prometheus/ses_nodes/{{ minion }}.yml:
  file.managed:
    - user: root
    - group: root
    - mode: 644
    - makedirs: True
    - fire_event: True
    - source: salt://ceph/monitoring/prometheus/files/minion.yml.j2
    - template: jinja
    - context:
        minion: {{ minion }}
{% endfor %}
