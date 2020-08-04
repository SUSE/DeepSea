
ganesha_config pool:
  cmd.run:
    - name: "ceph osd pool create ganesha_config 1 1"
    - unless: "ceph osd pool ls | grep -q ganesha_config"
    - fire_event: True

ganesha_config application:
  cmd.run:
    - name: "ceph osd pool application enable ganesha_config nfs"
    - fire_event: True

{# Reconfigure Ganesha to use dedicated pool #}

{% set nfs_pool = salt['deepsea.find_pool'](['cephfs', 'rgw']) %}

{# If the original pool does not exist or has no files, then skip migrating #}

{% if nfs_pool !=  None %}
{% set files = salt['cmd.run']('rados -p ' + nfs_pool + ' -N ganesha ls') %}
{% if files != "" %}

{% set tmpdir = salt['cmd.run']("mktemp -d") %}

extract configurations:
  cmd.run:
    - name: "for c in `rados -p {{ nfs_pool }} -N ganesha ls`; do rados -p {{ nfs_pool }} -N ganesha get $c $c; done"
    - cwd: {{ tmpdir }}
    - failhard: True

correct url:
  cmd.run:
    - name: "sed -i 's!{{ nfs_pool }}!ganesha_config!g' conf-*"
    - cwd: {{ tmpdir }}
    - failhard: True

import configurations:
  cmd.run:
    - name: "for c in *; do rados -p ganesha_config -N ganesha put $c $c; done"
    - cwd: {{ tmpdir }}
    - failhard: True


{{ tmpdir }}:
  file.absent

{% endif %}
{% endif %}

configure dashboard:
  cmd.run:
    - name: "ceph dashboard set-ganesha-clusters-rados-pool-namespace ganesha_config/ganesha"

