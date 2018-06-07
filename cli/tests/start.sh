#!/bin/bash

NUM_MINIONS=2
MINION_PORT=4000
INTERACTIVE=false
TIMEOUT=120

while getopts "imt:" opt; do
    case "$opt" in
    i)
        INTERACTIVE=true
        ;;
    m)  NUM_MINIONS=$OPTARG
        ;;
    t)  TIMEOUT=$OPTARG
        ;;
    esac
done

cat > /minion.template <<EOF
master: localhost
id: #MINION_ID#
user: root

tcp_pub_port: #MINION_PUB_PORT#
tcp_pull_port: #MINION_PULL_PORT#

pidfile: /var/run/salt-#MINION_ID#.pid
root_dir: /
conf_file: /etc/salt/#MINION_ID#
#pki_dir: /etc/salt/pki/minion
#cachedir: /var/cache/salt/minion
#sock_dir: /var/run/salt/minion
append_minionid_config_dirs: [cachedir, pki_dir, sock_dir]

log_file: /var/log/salt/#MINION_ID#
# The level of messages to send to the console.
# One of 'garbage', 'trace', 'debug', info', 'warning', 'error', 'critical'.
#log_level: warning
EOF

echo "minion1" > /etc/salt/minion_id

echo "Starting salt-master..."
salt-master -u salt -d

salt-run state.event > /var/log/salt.event.log &

PUB_PORT=$MINION_PORT
PULL_PORT=$(($PUB_PORT + 1))
cat /minion.template | sed -e "s/#MINION_ID#/minion1/g" \
                            -e "s/#MINION_PUB_PORT#/$PUB_PORT/g" \
                            -e "s/#MINION_PULL_PORT#/$PULL_PORT/g" \
                        > /etc/salt/minion
MINION_PORT=$(($MINION_PORT + 2))

echo "Starting salt-minion minion1 ..."
salt-minion -d

for i in `seq 2 $NUM_MINIONS`; do
    mkdir -p /etc/salt/minion$i
    PUB_PORT=$MINION_PORT
    PULL_PORT=$(($PUB_PORT + 1))
    cat /minion.template | sed -e "s/#MINION_ID#/minion$i/g" \
                               -e "s/#MINION_PUB_PORT#/$PUB_PORT/g" \
                               -e "s/#MINION_PULL_PORT#/$PULL_PORT/g" \
                         > /etc/salt/minion$i/minion
    MINION_PORT=$(($MINION_PORT + 2))

    echo "Starting salt-minion minion$i ..."
    salt-minion -c /etc/salt/minion$i -d
done


echo "Waiting for salt-minions to connect with salt-master..."
for i in `seq $NUM_MINIONS`; do
    BTIME=`date +%s`
    while true; do
        FOUND=`grep "^salt/auth" /var/log/salt.event.log | grep "minion$i" | wc -l`
        [ "$FOUND" -gt "0" ] && break
        sleep 1
        ETIME=`date +%s`
        if [ $(($ETIME - $BTIME)) -gt $TIMEOUT ]; then
            echo "TIMEOUT ERROR: salt-minions did not connect in time"
            exit 1
        fi
    done
    echo "salt-minion minion$i connected."
done

echo "Accepting minion keys..."
salt-key -Ay

echo "Waiting for salt-minion to start..."
for i in `seq $NUM_MINIONS`; do
    BTIME=`date +%s`
    while true; do
        FOUND=`grep "^minion_start" /var/log/salt.event.log | grep "minion$i" | wc -l`
        [ "$FOUND" -gt "0" ] && break
        sleep 1
        ETIME=`date +%s`
        if [ $(($ETIME - $BTIME)) -gt $TIMEOUT ]; then
            echo "TIMEOUT ERROR: salt-minions did not start in time"
            exit 1
        fi
    done
    echo "salt-minion minion$i started."
done


kill `pgrep salt-run`

echo "Testing minion response..."
salt \* test.ping

cd /deepsea/cli

pytest --cov=. -v tests
coverage html

if $INTERACTIVE; then
    /bin/bash
fi

rm -rf tests/__pycache__
