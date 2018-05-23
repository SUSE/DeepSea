# This is an example file to give you some hints on how the strucutre should look like
# By adjusting this file you can prevent the 'cephprocesses' module from failing if a
# specified OSD is down. This can come in handy when you have a OSD/device that is known
# the be failing but can't be removed for whatever reason.

# Example:
#
#blacklist:
#  ceph-osd:
#    - 0
#    - 223
#    - 72
#
# This would exclude OSDs with ids 0, 223 and 72 from the checks.
#
# Currently there is only support for blacklisting OSDs.
