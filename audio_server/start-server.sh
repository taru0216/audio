#!/bin/sh

RUN_SERVER="python lib/makuhari/audio_server/server.py localhost:8888"

if test "x$DBUS_SESSION_BUS_ADDRESS" = "x"; then
  RUN_SERVER="dbus-launch --exit-with-session --auto-syntax $RUN_SERVER"
fi

$RUN_SERVER
