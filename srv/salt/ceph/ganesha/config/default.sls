
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
      role: {{ role }}
    - fire_event: True

{% endfor %}

