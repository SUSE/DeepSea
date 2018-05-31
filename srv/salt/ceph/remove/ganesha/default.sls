remove ganesha nop:
  test.nop

{% if salt.saltutil.runner('select.minions', cluster='ceph', roles='ganesha') == [] %}

{% for role in salt['pillar.get']('ganesha_configurations', [ 'ganesha' ]) %}
{% for host in salt.saltutil.runner('select.minions', cluster='ceph', roles=role, host=True) %}
{% set keyring = "client." + role + "." + host %}

auth {{ keyring }}:
  cmd.run:
    - name: "ceph auth del {{ keyring }}"

{% endfor %}
{% endfor %}
{% endif %}

fix salt job cache permissions:
  cmd.run:
  - name: "find /var/cache/salt/master/jobs -user root -exec chown {{ salt['deepsea.user']() }}:{{ salt['deepsea.group']() }} {} ';'"

