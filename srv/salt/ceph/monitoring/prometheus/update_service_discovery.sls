
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

/etc/prometheus/ses_nodes:
  file.directory:
    - user: root
    - group: root
    - file_mode: 644
    - dir_mode: 755
    - clean: True
    - makedirs: True
{% if salt.saltutil.runner('select.minions', cluster='ceph', host=False) %}
    - require:
{% for minion in salt.saltutil.runner('select.minions', cluster='ceph', host=False) %}
       - file: /etc/prometheus/ses_nodes/{{ minion }}.yml
{% endfor %}
{% endif %}

