{% set dashboard_user = salt['pillar.get']('dashboard_user', 'admin') %}
{% set dashboard_pw = salt['pillar.get']('dashboard_password', salt['grains.get']('dashboard_creds:' ~ dashboard_user , salt['random.get_str'](10))) %}

enable ceph dashboard:
  cmd.run:
    - name: ceph mgr module enable dashboard
    - failhard: True

create self signed certificate:
  cmd.run:
    - name: ceph dashboard create-self-signed-cert
    - failhard: True

dashboard user exists:
  cmd.run:
    - name: /bin/true
    - unless: ceph dashboard ac-user-show -f json | jq -e 'index("{{ dashboard_user }}")'

set username and password:
  cmd.run:
    # This command is printed although the 'onchange' statement evaluates as true. This might cause confusion.
    - name: ceph dashboard ac-user-create {{ dashboard_user }} {{ dashboard_pw }} administrator
    - onchanges:
        - cmd: dashboard user exists

set dashboard password grain:
  module.run:
    - name: grains.set
    - key: dashboard_creds:{{ dashboard_user }}
    - val: {{ dashboard_pw }}
    - onchanges:
        - cmd: set username and password
