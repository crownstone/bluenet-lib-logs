import os
import re
import logging

_LOGGER = logging.getLogger(__name__)

class LogLineRetriever:
    def __init__(self):
        self.logPattern = re.compile(".*?cs_log_args\((.*)")


        self.sourceFilesDir = None

        self.cacheFiles = False

        # Key: filename
        # Data: all lines in file as list.
        self.bluenetFiles = {}

        # Key: filename hash.
        # Data: filename.
        self.fileNameHashMap = {}

        # A list with the full path of all the source files (and maybe some more).
        self.fileNames = []

        self.cache = {}

    # We could also get all source files from: build/default/CMakeFiles/crownstone.dir/depend.internal
    def setSourceFilesDir(self, dir: str):
        if os.path.isdir(dir) == False:
            _LOGGER.warning(f"No such dir: {dir}")

        self.sourceFilesDir = dir

        self._parseFiles()
        # print(self.cache)

    def _parseFiles(self):
        """
        Cache all C/C++ fileNames in sourceFilesDir
        """
        for root, dirs, files in os.walk(self.sourceFilesDir):
            for fileName in files:
                if fileName.endswith((".cpp.ii", ".c.i", ".hpp.ii")):
                    self._parseFile(os.path.join(root, fileName))

    def _parseFile(self, fileName):
        file = open(fileName, "r")
        lines = file.readlines()
        file.close()

        mergedLine = ""
        mergingMultiLine = False
        bracketOpenCount = 0
        for line in lines:
            if line.startswith('#'):
                # Skip comments.
                continue
            if mergingMultiLine:
                mergedLine += line.strip()
                bracketOpenCount += self._countBrackets(line)

                if bracketOpenCount == 0:
                    mergingMultiLine = False
                    # print(f"Merged multiline: {mergedLine}")
                    self._parseLogLine(mergedLine)
                continue
            match = self.logPattern.match(line)
            if match:
                bracketOpenCount = self._countBrackets(line)
                if bracketOpenCount > 0:
                    # This is probably a multi line log.
                    mergingMultiLine = True
                    mergedLine = line.strip()
                    continue
                if bracketOpenCount < 0:
                    print(f"Too many closing brackets:")
                    print(f"File: {fileName}")
                    print(f"Line: {line}")
                    return
                self._parseLogLine(line)

    def _parseLogLine(self, line):
        # print(f"Found: {line}")
        match = self.logPattern.match(line)
        (endIndex, logArgs) = self._getArgs(match.group(1), 0)
        logCode = match.group(1)[0:endIndex]
        # print(match.group(1))
        # print(logCode)
        # print(logArgs)
        if logArgs is None or not logArgs[0].startswith("fileNameHash("):
            return
        (endIndex, fileNameHashArgs) = self._getArgs(logArgs[0], len("fileNameHash("))
        # print(fileNameHashArgs)


        fileName = fileNameHashArgs[0][1:-1] # Remove quotes from string
        fileNameHash = self._getFileNameHash(fileName)
        lineNumber = int(logArgs[1])
        # logLevel = int(logArgs[2])
        # addNewLine = logArgs[3]
        logString = logArgs[4]
        # print(f"{fileNameHash} {lineNumber} {logString}")
        if fileNameHash not in self.cache:
            self.cache[fileNameHash] = {}

        self.cache[fileNameHash]["fileName"] = fileName
        self.cache[fileNameHash][lineNumber] = logString

    def _countBrackets(self, line):
        escape = False
        string = None # Can become either ' or "
        bracketOpenCount = 0
        for c in line:
            if escape:
                escape = False
                continue
            if c == '\\':
                escape = True
                continue

            if string != None:
                if c == string:
                    # End of string
                    string = None
                continue

            if c == '"' or c == "'":
                string = c
                # Start of string
                continue

            if c == '(':
                bracketOpenCount += 1
            if c == ')':
                bracketOpenCount -= 1
        return bracketOpenCount

    # Returns index of closing bracket, or None if not found
    # startIndex is index after the opening bracket
    def _getArgs(self, line, startIndex):
        escape = False
        string = None # Can become either ' or "
        bracketOpenCount = 1
        args = [""]
        for i in range(startIndex, len(line)):
            c = line[i]
            if escape:
                escape = False
                args[-1] += c
                continue
            if c == '\\':
                escape = True
                continue

            args[-1] += c
            if string != None:
                if c == string:
                    # End of string
                    string = None
                continue

            if c == '"' or c == "'":
                string = c
                # Start of string
                continue

            if c == '(':
                bracketOpenCount += 1
            if c == ')':
                bracketOpenCount -= 1
            if bracketOpenCount == 1 and c == ',':
                # Remove comma from arg
                args[-1] = args[-1][0:-1]
                args.append("")
            if bracketOpenCount == 0:
                # Remove the last closing bracket from the arg
                args[-1] = args[-1][0:-1]

                # Remove leading and trailing spaces from args
                for j in range(0, len(args)):
                    args[j] = args[j].strip()

                return i, args
        return None, None




    def getFileName(self, fileNameHash: int):
        if fileNameHash in self.cache:
            return self.cache[fileNameHash]["fileName"]
        return None

    def getLogFormat(self, fileName: str, lineNumber: int):
        fileNameHash = self._getFileNameHash(fileName)
        if fileNameHash in self.cache:
            return self.cache[fileNameHash][lineNumber]
        return None

    def _getFileNameHash(self, fileName: str):
        byteArray = bytearray()
        byteArray.extend(map(ord, fileName))

        hashVal: int = 5381
        # A string in C ends with 0.
        hashVal = (hashVal * 33 + 0) & 0xFFFFFFFF
        for c in reversed(byteArray):
            if c == ord('/'):
                return hashVal
            hashVal = (hashVal * 33 + c) & 0xFFFFFFFF
        return hashVal

if __name__ == "__main__":
    parser = LogLineRetriever()
    parser.setSourceFilesDir("/home/vliedel/dev/bluenet-workspace-cmake/bluenet/build/pca593/CMakeFiles/crownstone.dir/src")

