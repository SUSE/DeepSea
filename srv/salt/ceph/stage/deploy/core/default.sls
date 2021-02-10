{% set master = salt['master.minion']() %}

{% set FAIL_ON_WARNING = salt['pillar.get']('FAIL_ON_WARNING', 'True') %}

{% if salt['saltutil.runner']('ready.check', cluster='ceph', fail_on_warning=FAIL_ON_WARNING)  == False %}
ready check failed:
  salt.state:
    - name: "Fail on Warning is True"
    - tgt: {{ master }}
    - failhard: True

{% endif %}

{# This checks for config file changes and sets restart grains if necessary   #}
{# (the config_has_changed value is unused, but is necessary in order for the #}
{# runner to actually be invoked in this context) #}
{% set config_has_changed = salt['saltutil.runner']('changed.any') %}

{# Salt orchestrate ignores return codes of other salt runners. #}
#validate:
#  salt.runner:
#    - name: validate.pillar

{# Until return codes fail correctly and the above can be uncommented, #}
{# rely on the side effect of the runner printing its output and failing #}
{# on a bogus state #}
{% if salt['saltutil.runner']('validate.pillar', cluster='ceph') == False %}
validate failed:
  salt.state:
    - name: just.exit
    - tgt: {{ master }}
    - failhard: True

{% endif %}


{% if salt['pillar.get']('time_service') != "disabled" %}
time:
  salt.state:
    - tgt: 'I@cluster:ceph'
    - tgt_type: compound
    - sls: ceph.time
{% endif %}

configuration check:
  salt.state:
    - tgt: {{ master }}
    - tgt_type: compound
    - sls: ceph.configuration.check
    - failhard: True

create ceph.conf:
  salt.state:
    - tgt: {{ master }}
    - sls: ceph.configuration.create
    - failhard: True

configuration:
  salt.state:
    - tgt: 'I@cluster:ceph'
    - tgt_type: compound
    - sls: ceph.configuration

admin:
  salt.state:
    - tgt: 'I@roles:admin and I@cluster:ceph or I@roles:master'
    - tgt_type: compound
    - sls: ceph.admin

mgr keyrings:
  salt.state:
    - tgt: 'I@roles:mgr and I@cluster:ceph'
    - tgt_type: compound
    - sls: ceph.mgr.keyring
    - failhard: True

monitors:
  salt.state:
    - tgt: 'I@roles:mon and I@cluster:ceph'
    - tgt_type: compound
    - sls: ceph.mon
    - failhard: True

mgr auth:
  salt.state:
    - tgt: {{ master }}
    - sls: ceph.mgr.auth

mgrs:
  salt.state:
    - tgt: 'I@roles:mgr and I@cluster:ceph'
    - tgt_type: compound
    - sls: ceph.mgr
    - failhard: True

crash auth:
  salt.state:
    - tgt: {{ master }}
    - sls: ceph.crash.auth

crash:
  salt.state:
    - tgt: 'I@cluster:ceph'
    - tgt_type: compound
    - sls: ceph.crash
    - failhard: True

install ca cert in mgr minions:
  salt.state:
    - tgt: 'I@roles:mgr and I@cluster:ceph'
    - tgt_type: compound
    - sls: ceph.ssl.distribute_ca
    - failhard: True

# Immediately after deploying ceph-mgr, it takes a few seconds for the
# various modules to become available.  If we don't wait for this, any
# subqeuent `ceph` commands that require mgr will fail (for example
# `ceph mgr module enable [...]`).
wait for mgr to be available:
  salt.function:
    - name: retry.cmd
    - tgt: {{ master }}
    - tgt_type: compound
    - kwarg:
        'cmd': 'test "$(ceph mgr dump | jq .available)" = "true"'

dashboard:
  salt.state:
    - tgt: {{ master }}
    - tgt_type: compound
    - sls: ceph.dashboard
    - failhard: True

## disabled for now
# mgr orchestrator module:
#   salt.state:
#     - tgt: {{ master }}
#     - tgt_type: compound
#     - sls: ceph.mgr.orchestrator
#     - pillar:
#         'salt_api_url': http://{{ master }}:8000/
#         'salt_api_username': admin
#         'salt_api_password': {{ salt.saltutil.runner('sharedsecret.show') }}
#     - failhard: True

osd auth:
  salt.state:
    - tgt: {{ master }}
    - tgt_type: compound
    - sls: ceph.osd.auth
    - failhard: True

sysctl:
  salt.state:
    - tgt: 'I@roles:storage and I@cluster:ceph'
    - tgt_type: compound
    - sls: ceph.sysctl
    - failhard: True

set osd keyrings:
  salt.state:
    - tgt: 'I@roles:storage and I@cluster:ceph'
    - tgt_type: compound
    - sls: ceph.osd.keyring
    - failhard: True

deploy osds:
  salt.runner:
    - name: disks.deploy
    - failhard: True

latency tuned:
  salt.state:
    - tgt: '( I@roles:mgr or I@roles:mon ) and I@cluster:ceph'
    - tgt_type: compound
    - sls: ceph.tuned.latency
    - failhard: True

{% set deepsea_minions = salt['saltutil.runner']('deepsea_minions.matches') %}
{% set mons = salt['saltutil.runner']('select.minions', roles='mon') %}
{% set mgrs = salt['saltutil.runner']('select.minions', roles='mgr') %}

{% set throughput_minions = deepsea_minions | difference(mons) | difference(mgrs) | join(',') %}


{% if throughput_minions != "" %}
throughput tuned:
  salt.state:
    - tgt: 'not ( I@roles:mgr or I@roles:mon ) and I@cluster:ceph'
    - tgt_type: compound
    - sls: ceph.tuned.throughput
    - failhard: True
{% endif %}

pools:
  salt.state:
    - tgt: {{ master }}
    - sls: ceph.pool
