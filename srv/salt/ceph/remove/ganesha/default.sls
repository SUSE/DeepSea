{% for role in salt['pillar.get']('ganesha_configurations', [ 'ganesha' ]) %}
{% for host in salt.saltutil.runner('select.minions', cluster='ceph', roles=role, host=True) %}
{% set keyring = "client." + role + "." + host %}

auth {{ keyring }}:
  cmd.run:
    - name: "ceph auth del {{ keyring }}"

{% endfor %}
{% endfor %}