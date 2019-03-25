# This is the default configuration for the storage enclosure LED blinking.
# The placeholder {device_file} will be replaced with the device file of
# the disk when the command is executed.
#
# Have a look into the /srv/pillar/ceph/README file to find out how to
# customize this configuration per minion/host.

disk_led:
  cmd:
    ident:
      'on': lsmcli local-disk-ident-led-on --path '{device_file}'
      'off': lsmcli local-disk-ident-led-off --path '{device_file}'
    fault:
      'on': lsmcli local-disk-fault-led-on --path '{device_file}'
      'off': lsmcli local-disk-fault-led-off --path '{device_file}'
