
{% set FAIL_ON_WARNING = salt['pillar.get']('FAIL_ON_WARNING', 'True') %}

{% if salt['saltutil.runner']('ready.check', cluster='ceph', fail_on_warning=FAIL_ON_WARNING)  == False %}
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
{% if salt['saltutil.runner']('validate.pillar', cluster='ceph') == False %}
validate failed:
  salt.state:
    - name: just.exit
    - tgt: {{ salt['pillar.get']('master_minion') }}
    - failhard: True

{% endif %}


{% if salt['pillar.get']('time_service') != "disabled" %}
time:
  salt.state:
    - tgt: 'I@cluster:ceph'
    - tgt_type: compound
    - sls: ceph.time
{% endif %}

packages:
  salt.state:
    - tgt: 'I@cluster:ceph'
    - tgt_type: compound
    - sls: ceph.packages

configuration check:
  salt.state:
    - tgt: {{ salt['pillar.get']('master_minion') }}
    - tgt_type: compound
    - sls: ceph.configuration.check
    - failhard: True

create ceph.conf:
  salt.state:
    - tgt: {{ salt['pillar.get']('master_minion') }}
    - sls: ceph.configuration.create
    - failhard: True

configuration:
  salt.state:
    - tgt: 'I@cluster:ceph'
    - tgt_type: compound
    - sls: ceph.configuration

# this gets pre-parsed anyways.. maybe put this ontop
# replace with changed.all runner
{% set ret_mon = salt.saltutil.runner('changed.mon') %}
{% set ret_osd = salt['saltutil.runner']('changed.osd') %}
{% set ret_mgr = salt['saltutil.runner']('changed.mgr') %}
{% for config in salt['pillar.get']('rgw_configurations', [ 'rgw' ]) %}
{% set ret_rgw_conf = salt.saltutil.runner('changed.config', role_name=config) %}
{% endfor %}
{% set ret_client = salt['saltutil.runner']('changed.client') %}
{% set ret_global = salt['saltutil.runner']('changed.global') %}
{% set ret_mds = salt['saltutil.runner']('changed.mds') %}
{% set ret_igw = salt['saltutil.runner']('changed.igw') %}

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
    - tgt: {{ salt['pillar.get']('master_minion') }}
    - sls: ceph.mgr.auth

mgrs:
  salt.state:
    - tgt: 'I@roles:mgr and I@cluster:ceph'
    - tgt_type: compound
    - sls: ceph.mgr
    - failhard: True

setup ceph exporter:
  salt.state:
    - tgt: {{ salt['pillar.get']('master_minion') }}
    - tgt_type: compound
    - sls: ceph.monitoring.prometheus.exporters.ceph_exporter

setup rbd exporter:
  salt.state:
    - tgt: {{ salt['pillar.get']('master_minion') }}
    - tgt_type: compound
    - sls: ceph.monitoring.prometheus.exporters.rbd_exporter

osd auth:
  salt.state:
    - tgt: {{ salt['pillar.get']('master_minion') }}
    - tgt_type: compound
    - sls: ceph.osd.auth
    - failhard: True

sysctl:
  salt.state:
    - tgt: 'I@roles:storage and I@cluster:ceph'
    - tgt_type: compound
    - sls: ceph.sysctl
    - failhard: True

storage:
  salt.state:
    - tgt: 'I@roles:storage and I@cluster:ceph'
    - tgt_type: compound
    - sls: ceph.osd
    - failhard: True

grains:
  salt.state:
    - tgt: '{{ salt['pillar.get']('deepsea_minions') }}'
    - tgt_type: compound
    - sls: ceph.osd.grains
    - failhard: True

mgr tuned:
  salt.state:
    - tgt: 'I@roles:mgr and I@cluster:ceph'
    - tgt_type: compound
    - sls: ceph.tuned.mgr
    - failhard: True

mon tuned:
  salt.state:
    - tgt: 'I@roles:mon and I@cluster:ceph'
    - tgt_type: compound
    - sls: ceph.tuned.mon
    - failhard: True

osd tuned:
  salt.state:
    - tgt: 'I@roles:storage and I@cluster:ceph'
    - tgt_type: compound
    - sls: ceph.tuned.osd
    - failhard: True

pools:
  salt.state:
    - tgt: {{ salt['pillar.get']('master_minion') }}
    - sls: ceph.pool
