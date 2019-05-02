
validate upgrade pre-requesites:
  salt.runner:
    - name: ganesha_upgrade.validate
    - failhard: True

upgrade ganesha conf:
  salt.runner:
    - name: ganesha_upgrade.upgrade
    - failhard: True
