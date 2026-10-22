#!/bin/sh
# Start, stop or check the twin server in the background.
#   run.sh start | stop | status | key
# Server files (certificates, operator key, logs): $TWIN_DIR
TWIN_DIR=${TWIN_DIR:-$HOME/.local/share/lecture-tools/cps-twin}
PYTHON=${PYTHON:-$HOME/.local/share/lecture-tools/venv/bin/python}
here=$(dirname "$(readlink -f "$0")")
case $1 in
  start)
    if pgrep -f "$here/twin.py" > /dev/null; then echo "already running"; exit 0; fi
    nohup "$PYTHON" "$here/twin.py" --dir "$TWIN_DIR" >> "$TWIN_DIR/server.log" 2>&1 &
    sleep 2
    "$0" status ;;
  stop)
    pkill -f "$here/twin.py" || { echo "not running"; exit 0; }
    for i in 1 2 3 4 5 6 7 8 9 10; do
      pgrep -f "$here/twin.py" > /dev/null || { echo stopped; exit 0; }
      sleep 1
    done
    pkill -9 -f "$here/twin.py"; echo killed ;;
  status)
    if pgrep -f "$here/twin.py" > /dev/null; then echo "running, log: $TWIN_DIR/server.log"
    else echo "not running"; exit 1; fi ;;
  key)
    cat "$TWIN_DIR/operator.key" ;;
  *)
    echo "usage: $0 start|stop|status|key"; exit 2 ;;
esac
