
prevent empty rendering:
  test.nop:
    - name: skip

{% for role in salt['pillar.get']('ganesha_configurations', [ 'ganesha' ]) %}
{% for host in salt.saltutil.runner('select.minions', cluster='ceph', roles=role, host=True) %}
{% set client = "client." + role + "." + host %}
{% set keyring_file = salt['keyring.file']('ganesha', client)  %}

auth {{ keyring_file }}:
  cmd.run:
    - name: "ceph auth add {{ client }} -i {{ keyring_file }}"
    - fire_event: True

{% set rgw_role = salt['rgw.configuration'](role) %}
{% if rgw_role %}
{% set rgw_keyring_file = "/srv/salt/ceph/ganesha/cache/client." + rgw_role + "." + role + "." + host + ".keyring" %}
{% set rgw_client = "client." + rgw_role + "." + role + "." + host %}

auth {{ rgw_keyring_file }}:
  cmd.run:
    - name: "ceph auth add {{ rgw_client }} -i {{ rgw_keyring_file }}"
    - fire_event: True

{% endif %}

{% endfor %}
{% endfor %}

fix salt job cache permissions:
  cmd.run:
  - name: "find /var/cache/salt/master/jobs -user root -exec chown {{ salt['deepsea.user']() }}:{{ salt['deepsea.group']() }} {} ';'"

