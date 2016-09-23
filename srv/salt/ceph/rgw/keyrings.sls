
{% for role in salt['pillar.get']('rgw_configurations', [ 'rgw' ]) %}
{% for host in salt.saltutil.runner('select.minions', cluster='ceph', roles=role, host=True) %}
{% set client = "client." + role + "." + host %}
{% set keyring_file = "/srv/salt/ceph/rgw/cache/" + client + ".keyring" %}
{{ keyring_file}}:
  file.managed:
    - source: 
      - salt://ceph/rgw/files/{{ role }}.j2
    - template: jinja
    - user: salt
    - group: salt
    - mode: 600
    - makedirs: True
    - context:
      client: {{ client }}
      secret: {{ salt['keyring.secret'](keyring_file) }}
    - fire_event: True

auth {{ keyring_file }}:
  cmd.run:
    - name: "ceph auth add {{ client }} -i {{ keyring_file }}"

{% endfor %}
{% endfor %}


