{% for host in salt.saltutil.runner('select.minions', cluster='ceph', roles='mon', host=True) %}

    restarting mons on {{ host }}:
      salt.state:
        - tgt: {{ host }}
        - tgt_type: compound
        - sls: ceph.mon.restart
        - failhard: True

{% endfor %}

{% for host in salt.saltutil.runner('select.minions', cluster='ceph', roles='storage', host=True) %}

    restarting osds on {{ host }}:
      salt.state:
        - tgt: {{ host }}
        - tgt_type: compound
        - sls: ceph.osd.restart
        - failhard: True

{% endfor %}

{% for host in salt.saltutil.runner('select.minions', cluster='ceph', roles='rgw', host=True) %}

    restarting rgw on {{ host }}:
      salt.state:
        - tgt: {{ host }}
        - tgt_type: compound
        - sls: ceph.rgw.restart
        - failhard: True

{% endfor %}

{% for host in salt.saltutil.runner('select.minions', cluster='ceph', roles='mds', host=True) %}

    restarting mds on {{ host }}:
      salt.state:
        - tgt: {{ host }}
        - tgt_type: compound
        - sls: ceph.mds.restart
        - failhard: True

{% endfor %}

{% for host in salt.saltutil.runner('select.minions', cluster='ceph', roles='igw', host=True) %}

    restarting igw on {{ host }}:
      salt.state:
        - tgt: {{ host }}
        - tgt_type: compound
        - sls: ceph.igw.restart
        - failhard: True

{% endfor %}
