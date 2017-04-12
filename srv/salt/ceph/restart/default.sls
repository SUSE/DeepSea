{% set master = salt['pillar.get']('master_minion') %}
{% for host in salt.saltutil.runner('select.minions', cluster='ceph', roles='mon') %}

    wait until {{ host }} with role mon can be restarted:
      salt.state:
        - tgt: {{ master }}
        - sls: ceph.wait


    restarting mons on {{ host }}:
      salt.state:
        - tgt: {{ host }}
        - tgt_type: compound
        - sls: ceph.mon.restart
        - failhard: True

{% endfor %}

{% for host in salt.saltutil.runner('select.minions', cluster='ceph', roles='storage') %}
    
    wait until {{ host }} with role osd can be restarted:
      salt.state:
        - tgt: {{ master }}
        - sls: ceph.wait

    restarting osds on {{ host }}:
      salt.state:
        - tgt: {{ host }}
        - tgt_type: compound
        - sls: ceph.osd.restart
        - failhard: True

{% endfor %}

{% for host in salt.saltutil.runner('select.minions', cluster='ceph', roles='rgw') %}

    wait until {{ host }} with role rgw can be restarted:
      salt.state:
        - tgt: {{ master }}
        - sls: ceph.wait


    restarting rgw on {{ host }}:
      salt.state:
        - tgt: {{ host }}
        - tgt_type: compound
        - sls: ceph.rgw.restart
        - failhard: True

{% endfor %}

{% for host in salt.saltutil.runner('select.minions', cluster='ceph', roles='mds') %}
    
    wait until {{ host }} with role mds can be restarted:
      salt.state:
        - tgt: {{ master }}
        - sls: ceph.wait

    restarting mds on {{ host }}:
      salt.state:
        - tgt: {{ host }}
        - tgt_type: compound
        - sls: ceph.mds.restart
        - failhard: True

{% endfor %}

{% for host in salt.saltutil.runner('select.minions', cluster='ceph', roles='igw') %}
    
    wait until {{ host }} with role igw can be restarted:
      salt.state:
        - tgt: {{ master }}
        - sls: ceph.wait

    restarting igw on {{ host }}:
      salt.state:
        - tgt: {{ host }}
        - tgt_type: compound
        - sls: ceph.igw.restart
        - failhard: True

{% endfor %}

{% for host in salt.saltutil.runner('select.minions', cluster='ceph', roles='ganesha') %}
    
    wait until {{ host }} with role ganesha can be restarted:
      salt.state:
        - tgt: {{ master }}
        - sls: ceph.wait

    restarting ganesha on {{ host }}:
      salt.state:
        - tgt: {{ host }}
        - tgt_type: compound
        - sls: ceph.ganesha.restart
        - failhard: True

{% endfor %}
