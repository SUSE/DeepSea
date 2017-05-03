
storage nop:
  test.nop

{% if 'storage' not in salt['pillar.get']('roles') %}


terminate osds:
  module.run:
  - name: retry.pkill
  - kwargs:
      pattern: "ceph-osd"

{% for id in salt['osd.list']() %}

# systemctl stop ceph-osd@id can hang
#stop osd.{{ id }}:
#  service.dead:
#    - name: ceph-osd@{{ id }}
#    - enable: False
#
# Does not work
#systemctl terminate osds:
#  cmd.run:
#    - name: "systemctl kill ceph-osd*"
#
#systemctl kill osds:
#  cmd.run:
#    - name: "systemctl kill --signal=9 ceph-osd*"

{% endfor %}


{# 33 * 4096.  See https://en.wikipedia.org/wiki/GUID_Partition_Table #}

{% for device, path in salt['osd.pairs']() %}

{% set end_of_disk = salt['cmd.run']('blockdev --getsz ' + device) | int %}
{% set seek_position = end_of_disk / 4096 - 33 %}

umount {{ path }}:
  module.run:
  - name: retry.cmd
  - kwargs:
      cmd: "umount {{ path }}"

{% for partition in [ 1, 2 ] %}

wipe partition {{ device }}{{ partition }}:
  cmd.run:
    - name: "dd if=/dev/zero of={{ device }}{{ partition }} bs=4096 count=1 oflag=direct"
    - onlyif: "test -b {{ device }}{{ partition }}"

{% endfor %}

sgdisk {{ device }}:
  cmd.run:
    - name: "sgdisk -Z --clear -g {{ device }}"

wipe gpt backups {{ device }}:
  cmd.run:
    - name: "dd if=/dev/zero of={{ device }} bs=4096 count=33 seek={{ seek_position | int }} oflag=direct"

udev settle {{ device }}:
  cmd.run:
    - name: "udevadm settle --timeout=60"

partprobe {{ device }}:
  cmd.run:
    - name: "partprobe {{ device }}"

udev settle {{ device }} again:
  cmd.run:
    - name: "udevadm settle --timeout=60"

{% endfor %}

include:
- .keyring

save grains:
  module.run:
    - name: osd.retain

{% endif %}
