
prevent empty rendering:
  test.nop:
    - name: skip

{% for role in salt['pillar.get']('ganesha_configurations', [ 'ganesha' ]) %}
check {{ role }}:
  file.exists:
    - name: /srv/salt/ceph/ganesha/files/{{ role }}.j2
    - failhard: True

{% for host in salt.saltutil.runner('select.minions', cluster='ceph', roles=role, host=True) %}
{% set client = "client." + role + "." + host %}
{% set keyring_file = salt['keyring.file']('ganesha', client)  %}


{{ keyring_file}}:
  file.managed:
    - source: 
      - salt://ceph/ganesha/files/{{ role }}.j2
    - template: jinja
    - user: salt
    - group: salt
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

