#!/usr/bin/make -f

DISTFILE := makuhari-0.1.tar.gz

DBUS_ADDRESS_FILE:=$(shell tempfile)
DBUS_PID_FILE:=$(shell tempfile)
RUN_DBUS=dbus-daemon --session --print-address 1 --print-pid 2 --fork

#PLAY=while true; do gst-launch filesrc location=Connect.mp3 ! decodebin ! audioconvert ! audioresample ! jackaudiosink sync=false buffer-time=180000; done
#PLAY=while true; do gst-launch fdsrc fd=0 < Connect.mp3 ! decodebin ! audioconvert ! audioresample ! jackaudiosink sync=false buffer-time=180000; done
PLAY=src/server.py

APT_INSTALL = sudo apt-get -y install

JACK_PLUMBING_RULE='(connect "gst-launch-0.10:out_jackaudiosink0_(.*)" "test-launch.*:in_jackaudiosrc.*_\\1")'
JACK_PLUMBING_CONF_FILE:=$(shell tempfile)

TEMPS = $(DBUS_ADDRESS_FILE) $(DBUS_PID_FILE) $(JACK_PLUMBING_CONF_FILE)

all: test-launch /usr/bin/jackd /usr/bin/gst-launch
	$(RUN_DBUS) > $(DBUS_ADDRESS_FILE)  2> $(DBUS_PID_FILE)
	DBUS_SESSION_BUS_ADDRESS=`cat $(DBUS_ADDRESS_FILE)` jack_control start
	echo $(JACK_PLUMBING_RULE) > $(JACK_PLUMBING_CONF_FILE)
	DBUS_SESSION_BUS_ADDRESS=`cat $(DBUS_ADDRESS_FILE)` jack.plumbing $(JACK_PLUMBING_CONF_FILE) &
	./test-launch "jackaudiosrc ! audioconvert ! ffenc_aac ! queue ! rtpmp4apay name=pay0" &
	$(PLAY)
	DBUS_SESSION_BUS_ADDRESS=`cat $(DBUS_ADDRESS_FILE)` jack_control stop
	kill $$(cat $(DBUS_PID_FILE))
	/bin/rm -f $(TEMPS)

test-launch: /usr/share/doc/libgstrtspserver-0.10-dev/examples/test-launch.c /usr/lib/i386-linux-gnu/gstreamer-0.10/libgstmad.so /usr/lib/gstreamer-0.10/libgstffmpeg.so
	gcc -o $@ $< `pkg-config gst-rtsp-server-0.10 --cflags --libs`

/usr/bin/jackd:
	$(APT_INSTALL) jack-tools jackd dbus

/usr/share/doc/libgstrtspserver-0.10-dev/examples/test-launch.c:
	$(APT_INSTALL) libgstrtspserver-0.10-dev

/usr/lib/i386-linux-gnu/gstreamer-0.10/libgstmad.so:
	$(APT_INSTALL) gstreamer0.10-plugins-ugly

/usr/lib/gstreamer-0.10/libgstffmpeg.so:
	$(APT_INSTALL) gstreamer0.10-ffmpeg

/usr/bin/gst-launch:
	$(APT_INSTALL) gstreamer-tools

dist:
	tar zcvf $(DISTFILE) lib demo deploy.mk setup.py

clean:
	killall dbus-daemon jack.plumbing test-launch || true
	/bin/rm -f test-launch $(DISTFILE) src/*.pyc
