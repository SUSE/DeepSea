
{% set master = salt['master.minion']() %}

openattic nop:
    test.nop

{% if salt.saltutil.runner('select.minions', cluster='ceph', roles='openattic') %}

openattic auth:
    salt.state:
        - tgt: {{ master }}
        - sls: ceph.openattic.auth

openattic:
    salt.state:
        - tgt: "I@roles:openattic"
        - tgt_type: compound
        - sls: ceph.openattic
        - pillar:
            'salt_api_shared_secret': {{ salt.saltutil.runner('sharedsecret.show') }}

openattic keyring:
    salt.state:
        - tgt: "I@roles:openattic"
        - tgt_type: compound
        - sls: ceph.openattic.keyring

openattic oaconfig:
    salt.state:
        - tgt: "I@roles:openattic"
        - tgt_type: compound
        - sls: ceph.openattic.oaconfig

{% endif %}
