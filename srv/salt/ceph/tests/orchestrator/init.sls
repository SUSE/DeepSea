"ceph orchestrator status | grep 'Backend: deepsea'":
  cmd.run

"ceph orchestrator status | grep 'Available: True'":
  cmd.run

# This is very rough, but at least gives us the assurance that
# `ceph orchestrator service ls` does print out at least two lines of
# service status for mon and mgr instances, thus demonstrating that
# the orchestrator module can talk to deepsea to find out what's running
'test "$(ceph orchestrator service ls | grep -e ^mon -e ^mgr | wc -l)" -gt 2':
  cmd.run

