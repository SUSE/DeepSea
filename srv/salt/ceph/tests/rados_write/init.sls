
enable application:
  cmd.run:
    - name: ceph osd pool application enable write_test deepsea_qa

create data:
  cmd.run:
    - name: "echo 'dummy content' > /tmp/verify.txt"

rados put:
  cmd.run:
    - name: rados -p write_test put test_object /tmp/verify.txt

rados get:
  cmd.run:
    - name: rados -p write_test get test_object /tmp/verify_returned.txt

compare:
  cmd.run:
    - name: cmp /tmp/verify.txt /tmp/verify_returned.txt
