#!/usr/bin/env python3

"""
An example that shows how to run a bluenet log client.

Run with `python3 logger.py --help` for information.
"""
import time
import argparse

from crownstone_uart import CrownstoneUart
from bluenet_logs import BluenetLogs


if __name__ == "__main__":
	parser = argparse.ArgumentParser(description="Configurable command line tool which decodes crownstone uart messages and prints them")
	parser.add_argument('-s', '--sourceDir',
						help='The path to the bluenet source code on your system. I.e. {BLUENET_GIT_REPO}/source/',
						default="/opt/bluenet-workspace/bluenet/source")
	parser.add_argument('-p','--usbPort',
						help="The usb port to use for UART communication with the crownstone. E.g. \"/dev/ttyACM0\"",
						default="/dev/ttyACM0")
	parsed_args = parser.parse_args()

	# Init bluenet logs, it will listen to events from the Crownstone lib.
	bluenetLogs = BluenetLogs()

	# Set the dir containing the bluenet source code files.
	bluenetLogs.setSourceFilesDir(parsed_args.sourceDir)

	# Init the Crownstone UART lib.
	uart = CrownstoneUart()
	uart.initialize_usb_sync(port=parsed_args.usbPort)

	# The try except part is just to catch a control+c to gracefully stop the UART lib.
	try:
		# Simply keep the program running.
		print(f"Listening for logs and using files in \"{parsed_args.sourceDir}\" to find the log formats.")
		while True:
			time.sleep(1)
	except KeyboardInterrupt:
		pass
	finally:
		print("\nStopping UART..")
		uart.stop()
		print("Stopped")
