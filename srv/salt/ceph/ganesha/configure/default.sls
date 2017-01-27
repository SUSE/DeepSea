{% for role in salt['ganesha.configurations']() %}
/etc/ganesha/ganesha.conf:
  file.managed:
    - source:
      - salt://ceph/ganesha/cache/{{role}}.conf
    - template: jinja
    - user: root
    - group: root
    - mode: 644
{% endfor %}