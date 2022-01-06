import json
import logging
import os

from crownstone_uart import UartEventBus, UartTopics
from crownstone_uart.core.uart.uartPackets.UartLogArrayPacket import UartLogArrayPacket
from crownstone_uart.core.uart.uartPackets.UartLogPacket import UartLogPacket

from bluenet_logs.LogFormatter import LogFormatter

_LOGGER = logging.getLogger(__name__)

class BluenetLogs:
	__version__ = "1.0.0"

	def __init__(self):
		self._logFormatter = LogFormatter()

		UartEventBus.subscribe(UartTopics.log, self._onLog)
		UartEventBus.subscribe(UartTopics.logArray, self._onLogArray)

		# The log string file name.
		self._logStringsFileName = ""

		# Modification timestamp of the log string file.
		self._logStringsFileTimestamp = 0

		# Key:   filename hash
		# Value: filename
		self._fileNames = {}

		# Key:   filename hash
		# Value: map with:
		#        Key:   line number
		#        Value: log string
		self._logs = {}

		# Key:   filename hash
		# Value: map with:
		#        Key:   line number
		#        Value: (startFormat, endFormat, separationFormat, elementFormat)
		self._logArrays = {}

	def setLogStringsFile(self, fileName: str):
		"""
		Set the file containing the log strings.
		It will be parsed and cached.
		If the file gets modified, it will be parsed and cached again.
		"""
		self._logStringsFileName = fileName
		self._importLogStringsFile()
		self._logStringsFileTimestamp = os.stat(fileName).st_mtime

	def _updateLogStrings(self):
		if self._isLogStringsFileUpdated():
			self._importLogStringsFile()

	def _isLogStringsFileUpdated(self) -> bool:
		fileName = self._logStringsFileName
		try:
			timestamp = os.stat(fileName).st_mtime
			if self._logStringsFileTimestamp != timestamp:
				self._logStringsFileTimestamp = timestamp
				return True
			return False
		except:
			return True

	def _importLogStringsFile(self):
		try:
			file = open(self._logStringsFileName, "r")
			logStringsJson = json.load(file)
			self._fileNames = {}
			self._logs = {}
			self._logArrays = {}
			for map in logStringsJson["source_files"]:
				fileNameHash = map["file_hash"]
				fileName = map["file_name"]
				self._fileNames[fileNameHash] = fileName

			for map in logStringsJson["logs"]:
				fileNameHash = map["file_hash"]
				lineNr = map["line_nr"]
				fmt = map["log_fmt"]
				if fileNameHash not in self._logs:
					self._logs[fileNameHash] = {}
				self._logs[fileNameHash][lineNr] = fmt

			for map in logStringsJson["logs_array"]:
				fileNameHash = map["file_hash"]
				lineNr = map["line_nr"]
				startFmt = map["start_fmt"]
				endFmt = map["end_fmt"]
				sepFmt = map["separator_fmt"]
				elementFmt = map["element_fmt"]
				if fileNameHash not in self._logArrays:
					self._logArrays[fileNameHash] = {}
				self._logArrays[fileNameHash][lineNr] = (startFmt, endFmt, sepFmt, elementFmt)
			_LOGGER.debug(f"Imported log strings from {self._logStringsFileName}")
		except Exception as e:
			_LOGGER.warning(f"Failed to import log strings from {self._logStringsFileName}: {e}")
			return

	def _onLog(self, data: UartLogPacket):
		self._updateLogStrings()
		if data.header.fileNameHash not in self._fileNames:
			_LOGGER.warning(f"No file name for {data.header}")
			return
		fileName = self._fileNames[data.header.fileNameHash]

		if data.header.lineNr not in self._logs[data.header.fileNameHash]:
			_LOGGER.warning(f"No log format for {fileName}:{data.header.lineNr}")
			return

		logFormat = self._logs[data.header.fileNameHash][data.header.lineNr]
		self._logFormatter.printLog(logFormat, fileName, data.header.lineNr, data.header.logLevel, data.header.newLine, data.argBufs)

	def _onLogArray(self, data: UartLogArrayPacket):
		self._updateLogStrings()
		if data.header.fileNameHash not in self._fileNames:
			_LOGGER.warning(f"No file name for {data.header}")
			return
		fileName = self._fileNames[data.header.fileNameHash]

		if data.header.lineNr not in self._logArrays[data.header.fileNameHash]:
			_LOGGER.warning(f"No log format for {fileName}:{data.header.lineNr}")
			return

		(startFormat, endFormat, separationFormat, elementFormat) = self._logArrays[data.header.fileNameHash][data.header.lineNr]
		self._logFormatter.printLogArray(startFormat, endFormat, separationFormat, elementFormat, fileName, data.header.lineNr, data.header.logLevel, data.header.newLine, data.elementType, data.elementSize, data.elementData)
