{% set master = salt['master.minion']() %}
{% for host in salt.saltutil.runner('select.minions', cluster='ceph', roles='openattic') %}

    wait until {{ host }} with role openattic can be restarted:
      salt.state:
        - tgt: {{ master }}
        - sls: ceph.wait
        - failhard: True

    check if openattic processes are still running on {{ host }} after restarting openattic:
      salt.state:
        - tgt: 'I@roles:openattic'
        - tgt_type: compound
        - sls: ceph.processes.openattic
        - failhard: True

    restarting openattic on {{ host }}:
      salt.state:
        - tgt: {{ host }}
        - tgt_type: compound
        - sls: ceph.openattic.restart
        - failhard: True

{% endfor %}
