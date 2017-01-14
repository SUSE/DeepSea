
{# silver, silver-common, gold, platinum, red, blue #}
{# need the context role to be silver, silver, gold, platinum, red, blue #}
{# red and blue are cephfs configs #}

{% for role in salt['pillar.get']('ganesha_configurations', [ 'ganesha' ]) %}
/srv/salt/ceph/ganesha/cache/{{ role }}.conf:
  file.managed:
    - source:
      - salt://ceph/ganesha/files/{{ role }}.conf.j2
    - template: jinja
    - makedirs: True
    - user: root
    - group: root
    - mode: 644 
    - context:
      role: {{ salt['rgw.configuration'](role) }}
    - fire_event: True

{% endfor %}

