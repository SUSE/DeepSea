{% set master = salt['pillar.get']('master_minion') %}
{% for host in salt.saltutil.runner('select.minions', cluster='ceph', roles='storage') %}
    
    wait until {{ host }} with role osd can be restarted:
      salt.state:
        - tgt: {{ master }}
        - sls: ceph.wait
        - failhard: True

    check if all processes are still running on {{ host }} after restarting osds:
      salt.state:
        - tgt: '{{ salt['pillar.get']('deepsea_minions') }}'
        - tgt_type: compound
        - sls: ceph.processes
        - failhard: True

    restarting osds on {{ host }}:
      salt.state:
        - tgt: {{ host }}
        - tgt_type: compound
        - sls: ceph.osd.restart
        - failhard: True

    wait for osds to be "in" Ceph on {{ host }}:
      salt.state:
        - tgt: {{ master }}
        - tgt_type: compound
        - sls: ceph.wait.until.all_osds_in
        - failhard: True

{% endfor %}
