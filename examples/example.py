#!/usr/bin/env python3

"""
An example that shows how to run a bluenet log client.
"""
import time

from crownstone_uart import CrownstoneUart

from bluenet_logs import BluenetLogs

# Change this to the path with the extracted log strings on your system.
logStringsFile = "/opt/bluenet-workspace/bluenet/build/default/extracted_logs.json"

# Init bluenet logs, it will listen to events from the Crownstone lib.
bluenetLogs = BluenetLogs()

# Set the dir containing the bluenet source code files.
bluenetLogs.setLogStringsFile(logStringsFile)

# Init the Crownstone UART lib.
uart = CrownstoneUart()
uart.initialize_usb_sync(port="/dev/ttyACM0")

# The try except part is just to catch a control+c to gracefully stop the UART lib.
try:
	# Simply keep the program running.
	print(f"Listening for logs and using \"{logStringsFile}\" to find the log formats.")
	while True:
		time.sleep(1)
except KeyboardInterrupt:
	pass
finally:
	print("\nStopping UART..")
	uart.stop()
	print("Stopped")
