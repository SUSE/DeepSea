
{% set FAIL_ON_WARNING = salt['pillar.get']('FAIL_ON_WARNING', 'True') %}

{% if salt['saltutil.runner']('ready.check', name='ceph', fail_on_warning=FAIL_ON_WARNING)  == False %}
ready check failed:
  salt.state:
    - name: "Fail on Warning is True"
    - tgt: {{ salt['pillar.get']('master_minion') }}
    - failhard: True

{% endif %}

{# Salt orchestrate ignores return codes of other salt runners. #}
#validate:
#  salt.runner:
#    - name: validate.pillar

{# Until return codes fail correctly and the above can be uncommented, #}
{# rely on the side effect of the runner printing its output and failing #}
{# on a bogus state #}
{% if salt['saltutil.runner']('validate.pillar', name='ceph') == False %}
validate failed:
  salt.state:
    - name: just.exit
    - tgt: {{ salt['pillar.get']('master_minion') }}
    - failhard: True

{% endif %}

time:
  salt.state:
    - tgt: 'I@cluster:ceph'
    - tgt_type: compound
    - sls: ceph.time

packages:
  salt.state:
    - tgt: 'I@cluster:ceph'
    - tgt_type: compound
    - sls: ceph.packages

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

monitors:
  salt.state:
    - tgt: 'I@roles:mon and I@cluster:ceph'
    - tgt_type: compound
    - sls: ceph.mon
    - failhard: True

storage auth:
  salt.state:
    - tgt: {{ salt['pillar.get']('master_minion') }}
    - tgt_type: compound
    - sls: ceph.osd.auth
    - failhard: True

storage:
  salt.state:
    - tgt: 'I@roles:storage and I@cluster:ceph'
    - tgt_type: compound
    - sls: ceph.osd
    - failhard: True

pools:
  salt.state:
    - tgt: {{ salt.saltutil.runner('select.one_minion', cluster='ceph', roles='mon')}}
    - sls: ceph.pool
