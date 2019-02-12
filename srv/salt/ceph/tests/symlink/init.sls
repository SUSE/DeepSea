
# Find disk of first OSD
{% set osd_id = salt['osd.list']() %}
{% set disk = salt['osd.device'](osd_id[0]) %}

{% set working = salt['file.symlink'](disk + "1", "/tmp/working") %}
{% set broken = salt['file.symlink'](disk + "Z", "/tmp/broken") %}

{% set wdisk, wpart = salt['osd.split_partition']("/tmp/working") %}
{% set bdisk, bpart = salt['osd.split_partition']("/tmp/broken") %}

check working symlink:
  cmd.run:
    - name: '[ {{ wdisk }} == {{ disk }} ] && [ "1" == {{ wpart }} ]'

check broken symlink:
  cmd.run:
    - name: '[ {{ bdisk }} == None ] && [ None == {{ bpart }} ]'

Remove working symlink:
  module.run:
    - name: file.remove
    - path: "/tmp/working"

Remove broken symlink:
  module.run:
    - name: file.remove
    - path: "/tmp/broken"

