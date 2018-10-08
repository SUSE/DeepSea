{% set master = salt['master.minion']() %}
{% for host in salt.saltutil.runner('select.minions', cluster='ceph', roles='storage') %}

    wait until {{ host }} with role osd can be restarted:
      salt.state:
        - tgt: {{ master }}
        - sls: ceph.wait
        - failhard: True

    restarting osds on {{ host }}:
      salt.state:
        - tgt: {{ host }}
        - tgt_type: compound
        - sls: ceph.osd.restart.force

{% endfor %}
