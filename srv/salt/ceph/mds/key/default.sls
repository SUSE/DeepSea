
prevent empty rendering:
  test.nop:
    - name: skip

{% for host in salt.saltutil.runner('select.minions', cluster='ceph', roles='mds', host=True) %}
{% set name = salt['mds.get_name'](host) %}
{% set client = "mds." + name %}
{% set keyring_file = salt['keyring.file']('mds', name)  %}
{{ keyring_file}}:
  file.managed:
    - source: 
      - salt://ceph/mds/files/keyring.j2
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

fix salt job cache permissions:
  cmd.run:
  - name: "find /var/cache/salt/master/jobs -user root -exec chown {{ salt['deepsea.user']() }}:{{ salt['deepsea.group']() }} {} ';'"

