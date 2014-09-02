#!/bin/sh
# This file managed by Puppet
# Linux Standard Base comments
### BEGIN INIT INFO
# Provides:          mugsy
# Required-Start:    $local_fs $network $remote_fs
# Required-Stop:     $local_fs $network $remote_fs
# Should-Start:
# Should-Stop:
# Default-Start:     2 3 4 5
# Default-Stop:      0 1 6
# Short-Description: Mugsy
# Description:       Mugsy
### END INIT INFO

. /etc/init.d/functions

BINPATH=/var/mugsy/lib/mugsy
PIDFILE=/var/run/mugsy.pid
PROG=mugsy

start() {
    echo -n "Starting $PROG: "
    daemon "$BINPATH start"
    echo
    RETVAL=$?
}

stop() {
    echo -n "Stopping $PROG: "
    daemon "$BINPATH stop"
    echo
    RETVAL=$?
}

restart() {
    echo -n "Restarting $PROG: "
    daemon "$BINPATH restart"
    echo
    RETVAL=$?
}

case "$1" in
start)
    start
    ;;
restart)
    restart
    ;;
stop)
    stop
    ;;
status)
    status -p "$PIDFILE" -l $BINPATH $PROG
    RETVAL=$?
    ;;
*)
    echo "Usage: $0 <start|stop|status|restart>" >&2
    exit 3
    ;;
esac
exit $RETVAL
