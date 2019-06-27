{% set DEVICE = salt['subvolume.device']() %}

{% if DEVICE != "" %}

subvolume:
  cmd.run:
    - name: "btrfs subvolume create /var/lib/ceph"
    - unless: "btrfs subvolume list / | grep -q '@/var/lib/ceph$'"
    - failhard: True

fstab and mount:
  mount.mounted:
    - name: /var/lib/ceph
    - device: {{ DEVICE }}
    - fstype: btrfs
    - opts: subvol=@/var/lib/ceph
    - persist: True

{% else %}

root file system is not btrfs:
  test.nop

{% endif %}

