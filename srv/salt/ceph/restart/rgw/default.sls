{% if salt.saltutil.runner('changed.rgw') == True %}
{% set master = salt['pillar.get']('master_minion') %}
{% for host in salt.saltutil.runner('select.minions', cluster='ceph', roles='rgw') %}

    wait until {{ host }} with role rgw can be restarted:
      salt.state:
        - tgt: {{ master }}
        - sls: ceph.wait

    check if all processes are still running on {{ host }} after restarting rgws:
      salt.state:
        - tgt: '{{ salt['pillar.get']('deepsea_minions') }}'
        - tgt_type: compound
        - sls: ceph.processes
        - failhard: True

    restarting rgw on {{ host }}:
      salt.state:
        - tgt: {{ host }}
        - tgt_type: compound
        - sls: ceph.rgw.restart
        - failhard: True

{% endfor %}
{% endif %}
