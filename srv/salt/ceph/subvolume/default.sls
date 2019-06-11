
subvolume:
  cmd.run:
    - name: "btrfs subvolume create /var/lib/ceph"
    - unless: "btrfs subvolume list / | grep -q '@/var/lib/ceph$'"
    - failhard: True

{# sed is easier to explain/debug than file.replace #}
fstab:
  cmd.run:
    - name: "sed -i 's!LABEL=ROOT /var btrfs defaults,subvol=@/var 0 0!&\\\nLABEL=ROOT /var/lib/ceph btrfs defaults,subvol=@/var/lib/ceph 0 0!' /etc/fstab"
    - unless: "grep -q subvol=@/var/lib/ceph /etc/fstab"
    - failhard: True

mount:
  cmd.run:
    - name: "mount /var/lib/ceph"
    - unless: "mount | grep -q /var/lib/ceph"

