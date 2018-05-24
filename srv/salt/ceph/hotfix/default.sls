{% set os = salt['grains.get']('os') %}

{% if os == 'SUSE' %}

lock down sles salt version:
  module.run:
    - name: pkg.add_lock
    - packages: salt-master, salt-minion

{% elif os == 'Ubuntu' %}

lock down ubuntu salt version:
  module.run:
    - name: pkg.hold
    - packages: salt-master, salt-minion

{% endif %}

