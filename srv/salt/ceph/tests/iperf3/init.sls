
starting iperf3:
  module.run:
    - name: multi.iperf_server_cmd

check iperf3 up:
  cmd.run:
    - name: "pgrep iperf3"
    - failhard: True

stopping iperf3:
  module.run:
    - name: multi.kill_iperf_cmd

check iperf3 down:
  cmd.run:
    - name: "[ `pgrep -c iperf3` == 0 ]"

