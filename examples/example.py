#!/usr/bin/env python3

"""
An example that shows how to run a bluenet log client.
"""
import time

from crownstone_uart import CrownstoneUart

from bluenet_logs import BluenetLogs

# Change this to the path with the bluenet source code files on your system.
sourceFilesDir = "/opt/bluenet-workspace/bluenet/source"
sourceFilesDir = "/home/vliedel/dev/bluenet-workspace-cmake/bluenet/source"

# Init bluenet logs, it will listen to events from the Crownstone lib.
bluenetLogs = BluenetLogs()

# Set the dir containing the bluenet source code files.
bluenetLogs.setSourceFilesDir(sourceFilesDir)

# Init the Crownstone UART lib.
uart = CrownstoneUart()
uart.initialize_usb_sync(port="/dev/ttyACM0")

# The try except part is just to catch a control+c to gracefully stop the UART lib.
try:
	# Simply keep the program running.
	print(f"Listening for logs and using files in \"{sourceFilesDir}\" to find the log formats.")
	while True:
		time.sleep(1)
except KeyboardInterrupt:
	pass
finally:
	print("\nStopping UART..")
	uart.stop()
	print("Stopped")
