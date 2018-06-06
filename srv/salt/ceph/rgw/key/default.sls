prevent empty rendering:
  test.nop:
    - name: skip

{% for role in salt['pillar.get']('rgw_configurations', [ 'rgw' ]) %}
check {{ role }}:
  file.exists:
    - name: /srv/salt/ceph/rgw/files/{{ role }}.j2
    - failhard: True

{% for host in salt.saltutil.runner('select.minions', cluster='ceph', roles=role, host=True) %}
{% set client = "client." + role + "." + host %}
{% set keyring_file = salt['keyring.file']('rgw', client)  %}


{{ keyring_file}}:
  file.managed:
    - source:
      - salt://ceph/rgw/files/{{ role }}.j2
    - template: jinja
    - user: {{ salt['deepsea.user']() }}
    - group: {{ salt['deepsea.group']() }}
    - mode: 600
    - makedirs: True
    - context:
      client: {{ client }}
      secret: {{ salt['keyring.secret'](keyring_file) }}
    - fire_event: True

{% endfor %}
{% endfor %}

fix salt job cache permissions:
  cmd.run:
  - name: "find /var/cache/salt/master/jobs -user root -exec chown {{ salt['deepsea.user']() }}:{{ salt['deepsea.group']() }} {} ';'"

