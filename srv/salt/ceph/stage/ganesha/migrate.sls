{% if salt.saltutil.runner('select.minions', cluster='ceph', roles='ganesha') or salt.saltutil.runner('select.minions', cluster='ceph', ganesha_configurations='*') %}

validate upgrade pre-requesites:
  salt.runner:
    - name: ganesha_upgrade.validate
    - failhard: True

upgrade ganesha conf:
  salt.runner:
    - name: ganesha_upgrade.upgrade
    - failhard: True

{% endif %}
