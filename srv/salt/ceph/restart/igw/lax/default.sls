{% set master = salt['pillar.get']('master_minion') %}
{% for host in salt.saltutil.runner('select.minions', cluster='ceph', roles='igw') %}
    
    wait until {{ host }} with role igw can be restarted:
      salt.state:
        - tgt: {{ master }}
        - sls: ceph.wait
        - failhard: True

    check if all processes are still running on {{ host }} after restarting igws:
      salt.state:
        - tgt: 'I@roles:igw'
        - tgt_type: compound
        - sls: ceph.processes
        - failhard: True

    restarting igw on {{ host }}:
      salt.state:
        - tgt: {{ host }}
        - tgt_type: compound
        - sls: ceph.igw.restart
        - failhard: True

{% endfor %}
