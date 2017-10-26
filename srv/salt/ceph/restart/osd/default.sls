{% if salt.saltutil.runner('changed.osd') == True %}
{% set master = salt['pillar.get']('master_minion') %}
{% for host in salt.saltutil.runner('select.minions', cluster='ceph', roles='storage') %}
    
    wait until {{ host }} with role osd can be restarted:
      salt.state:
        - tgt: {{ master }}
        - sls: ceph.wait

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

{% endfor %}
{% endif %}
