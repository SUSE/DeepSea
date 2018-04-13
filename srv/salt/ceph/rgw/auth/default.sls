
prevent empty rendering:
  test.nop:
    - name: skip

{% for role in salt['pillar.get']('rgw_configurations', [ 'rgw' ]) %}
{% for host in salt.saltutil.runner('select.minions', cluster='ceph', roles=role, host=True) %}
{% set client = "client." + role + "." + host %}
{% set keyring_file = salt['keyring.file']('rgw', client)  %}

auth {{ keyring_file }}:
  cmd.run:
    - name: "ceph auth add {{ client }} -i {{ keyring_file }}"

{% endfor %}
{% endfor %}

/var/cache/salt/master/jobs:
  file.directory:
    - user: {{ salt['deepsea.user']() }}
    - group: {{ salt['deepsea.group']() }}
    - recurse:
      - user
      - group



