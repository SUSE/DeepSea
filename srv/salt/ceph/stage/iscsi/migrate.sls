{% if salt.saltutil.runner('select.minions', cluster='ceph', roles='igw') %}

validate iscsi upgrade pre-requesites:
  salt.runner:
    - name: iscsi_upgrade.validate
    - failhard: True

upgrade iscsi conf:
  salt.runner:
    - name: iscsi_upgrade.upgrade
    - failhard: True

{% endif%}
