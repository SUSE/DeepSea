{# silver, silver-common, gold, platinum, red, blue #}
{# need the context role to be silver, silver, gold, platinum, red, blue #}
{# red and blue are cephfs configs #}

prevent empty rendering:
  test.nop:
    - name: skip

{% set nfs_pool = "ganesha_config" %}

{% for role in salt['pillar.get']('ganesha_configurations', [ 'ganesha' ]) %}
check {{ role }}:
  file.exists:
    - name: /srv/salt/ceph/ganesha/files/{{ role }}.conf.j2
    - failhard: True

{% for host in salt.saltutil.runner('select.minions', cluster='ceph', roles=role, host=True) %}

/srv/salt/ceph/ganesha/cache/{{ role }}.{{ host }}.conf:
  file.managed:
    - source:
      - salt://ceph/ganesha/files/{{ role }}.conf.j2
    - template: jinja
    - makedirs: True
    - user: {{ salt['deepsea.user']() }}
    - group: {{ salt['deepsea.group']() }}
    - mode: 600
    - context:
      rgw_role: {{ salt['rgw.configuration'](role) }}
      host: {{ host }}
      ganesha_role: {{role}}
      nfs_pool: {{ nfs_pool }}
    - fire_event: True

{% endfor %}
{% endfor %}

fix salt job cache permissions:
  cmd.run:
  - name: "find /var/cache/salt/master/jobs -user root -exec chown {{ salt['deepsea.user']() }}:{{ salt['deepsea.group']() }} {} ';'"

