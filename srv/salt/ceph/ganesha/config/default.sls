{# silver, silver-common, gold, platinum, red, blue #}
{# need the context role to be silver, silver, gold, platinum, red, blue #}
{# red and blue are cephfs configs #}


prevent empty rendering:
  test.nop:
    - name: skip

{% for role in salt['pillar.get']('ganesha_configurations', [ 'ganesha' ]) %}
check {{ role }}:
  file.exists:
    - name: /srv/salt/ceph/ganesha/files/{{ role }}.conf.j2
    - failhard: True

{% for host in salt.saltutil.runner('select.minions', cluster='ceph', roles=role, host=True) %}
{% set user_id = role + "." + host %}
{% set client = "client." + user_id %}
{% set keyring_file = salt['keyring.file']('ganesha', client)  %}

/srv/salt/ceph/ganesha/cache/{{ role }}.{{ host }}.conf:
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
      user_id: {{ user_id }}
      host: {{ host }}
      secret_access_key: {{ salt['keyring.secret'](keyring_file) }}
      ganesha_role: {{role}}
    - fire_event: True

{% endfor %}
{% endfor %}
