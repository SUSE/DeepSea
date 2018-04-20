{% set master = salt['master.minion']() %}
{% for host in salt.saltutil.runner('select.minions', cluster='ceph', roles='rgw') %}

    wait until {{ host }} with role rgw can be restarted:
      salt.state:
        - tgt: {{ master }}
        - sls: ceph.wait
        - failhard: True

    check if rgw processes are still running on {{ host }} after restarting rgws:
      salt.state:
        - tgt: 'I@roles:rgw'
        - tgt_type: compound
        - sls: ceph.processes.rgw
        - failhard: True

    restarting rgw on {{ host }}:
      salt.state:
        - tgt: {{ host }}
        - tgt_type: compound
        - sls: ceph.rgw.restart
        - failhard: True

{% endfor %}
