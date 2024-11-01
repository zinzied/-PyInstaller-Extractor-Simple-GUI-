from __future__ import print_function
import sys, os, shutil
import struct
import marshal
import zlib
from uuid import uuid4 as uniquename
from colorama import init
from colorama import Fore, Style
from importlib.util import MAGIC_NUMBER
import customtkinter as ctk
from tkinter import filedialog, messagebox

class PyInstallerExtractorApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("PyInstaller Extractor")
        self.geometry("400x200")

        self.label = ctk.CTkLabel(self, text="Select a file to extract:")
        self.label.pack(pady=10)

        self.button = ctk.CTkButton(self, text="Browse", command=self.browse_file)
        self.button.pack(pady=10)

    def browse_file(self):
        file_path = filedialog.askopenfilename(
            title="Select an executable file",
            filetypes=[("Executable files", "*.exe"), ("All files", "*.*")]
        )
        if file_path:
            try:
                main(file_path)
                messagebox.showinfo("Success", "Extraction completed successfully.")
            except Exception as e:
                messagebox.showerror("Error", f"An error occurred: {e}")

init()
# imp is deprecated in Python3 in favour of importlib
if sys.version_info.major == 3:
    from importlib.util import MAGIC_NUMBER
    pyc_magic = MAGIC_NUMBER

# The rest of your code remains unchanged

class CTOCEntry:
    def __init__(self, position, cmprsdDataSize, uncmprsdDataSize, cmprsFlag, typeCmprsData, name):
        self.position = position
        self.cmprsdDataSize = cmprsdDataSize
        self.uncmprsdDataSize = uncmprsdDataSize
        self.cmprsFlag = cmprsFlag
        self.typeCmprsData = typeCmprsData
        self.name = name

class PyInstArchive:
    PYINST20_COOKIE_SIZE = 24           # For pyinstaller 2.0
    PYINST21_COOKIE_SIZE = 24 + 64      # For pyinstaller 2.1+
    MAGIC = b'MEI\014\013\012\013\016'  # Magic number which identifies pyinstaller

    def __init__(self, path):
        self.filePath = path

    def open(self):
        try:
            self.fPtr = open(self.filePath, 'rb')
            self.fileSize = os.stat(self.filePath).st_size
        except:
            print('[!] Error: Could not open {0}'.format(self.filePath))
            return False
        return True

    def close(self):
        try:
            self.fPtr.close()
        except:
            pass

    def checkFile(self):
        print('[+] Processing {0}'.format(self.filePath))
        # Check if it is a 2.0 archive
        self.fPtr.seek(self.fileSize - self.PYINST20_COOKIE_SIZE, os.SEEK_SET)
        magicFromFile = self.fPtr.read(len(self.MAGIC))

        if magicFromFile == self.MAGIC:
            self.pyinstVer = 20     # pyinstaller 2.0
            print('[+] Pyinstaller version: 2.0')
            return True

        # Check for pyinstaller 2.1+ before bailing out
        self.fPtr.seek(self.fileSize - self.PYINST21_COOKIE_SIZE, os.SEEK_SET)
        magicFromFile = self.fPtr.read(len(self.MAGIC))

        if magicFromFile == self.MAGIC:
            print('[+] Pyinstaller version: 2.1+')
            self.pyinstVer = 21     # pyinstaller 2.1+
            return True

        print('[!] Error : Unsupported pyinstaller version or not a pyinstaller archive')
        sys.exit()
        return False

    def getCArchiveInfo(self):
        try:
            if self.pyinstVer == 20:
                self.fPtr.seek(self.fileSize - self.PYINST20_COOKIE_SIZE, os.SEEK_SET)

                # Read CArchive cookie
                (magic, lengthofPackage, toc, tocLen, self.pyver) = \
                struct.unpack('!8siiii', self.fPtr.read(self.PYINST20_COOKIE_SIZE))

            elif self.pyinstVer == 21:
                self.fPtr.seek(self.fileSize - self.PYINST21_COOKIE_SIZE, os.SEEK_SET)

                # Read CArchive cookie
                (magic, lengthofPackage, toc, tocLen, self.pyver, pylibname) = \
                struct.unpack('!8siiii64s', self.fPtr.read(self.PYINST21_COOKIE_SIZE))

        except:
            print('[!] Error : The file is not a pyinstaller archive')
            return False

        print('[+] Python version: {0}'.format(self.pyver))

        # Overlay is the data appended at the end of the PE
        self.overlaySize = lengthofPackage
        self.overlayPos = self.fileSize - self.overlaySize
        self.tableOfContentsPos = self.overlayPos + toc
        self.tableOfContentsSize = tocLen

        print('[+] Length of package: {0} bytes'.format(self.overlaySize))
        return True

    def parseTOC(self):
        # Go to the table of contents
        self.fPtr.seek(self.tableOfContentsPos, os.SEEK_SET)

        self.tocList = []
        parsedLen = 0

        # Parse table of contents
        while parsedLen < self.tableOfContentsSize:
            (entrySize, ) = struct.unpack('!i', self.fPtr.read(4))
            nameLen = struct.calcsize('!iiiiBc')

            (entryPos, cmprsdDataSize, uncmprsdDataSize, cmprsFlag, typeCmprsData, name) = \
            struct.unpack( \
                '!iiiBc{0}s'.format(entrySize - nameLen), \
                self.fPtr.read(entrySize - 4))

            name = name.decode('utf-8').rstrip('\0')
            if len(name) == 0:
                name = str(uniquename())
                print('[!] Warning: Found an unamed file in CArchive. Using random name {0}'.format(name))

            self.tocList.append( \
                                CTOCEntry(                      \
                                    self.overlayPos + entryPos, \
                                    cmprsdDataSize,             \
                                    uncmprsdDataSize,           \
                                    cmprsFlag,                  \
                                    typeCmprsData,              \
                                    name                        \
                                ))

            parsedLen += entrySize
        print('[+] Found {0} files in CArchive'.format(len(self.tocList)))

    def _writeRawData(self, filepath, data):
        nm = filepath.replace('\\', os.path.sep).replace('/', os.path.sep).replace('..', '__')
        nmDir = os.path.dirname(nm)
        if nmDir != '' and not os.path.exists(nmDir): # Check if path exists, create if not
            os.makedirs(nmDir)

        with open(nm, 'wb') as f:
            f.write(data)

    def extractFiles(self):
        print('[+] Beginning extraction...please standby')
        extractionDir = os.path.join(os.getcwd(), os.path.basename(self.filePath) + '_extracted')

        if not os.path.exists(extractionDir):
            os.mkdir(extractionDir)

        os.chdir(extractionDir)

        for entry in self.tocList:
            basePath = os.path.dirname(entry.name)
            if basePath != '':
                # Check if path exists, create if not
                if not os.path.exists(basePath):
                    os.makedirs(basePath)

            self.fPtr.seek(entry.position, os.SEEK_SET)
            data = self.fPtr.read(entry.cmprsdDataSize)

            if entry.cmprsFlag == 1:
                data = zlib.decompress(data)
                # Malware may tamper with the uncompressed size
                # Comment out the assertion in such a case
                assert len(data) == entry.uncmprsdDataSize # Sanity Check

            if entry.typeCmprsData == b's':
                # s -> ARCHIVE_ITEM_PYSOURCE
                # Entry point are expected to be python scripts
                print('[+] Possible entry point: {0}.pyc'.format(entry.name))
                self._writePyc(entry.name + '.pyc', data)

            elif entry.typeCmprsData == b'M' or entry.typeCmprsData == b'm':
                # M -> ARCHIVE_ITEM_PYPACKAGE
                # m -> ARCHIVE_ITEM_PYMODULE
                # packages and modules are pyc files with their header's intact
                self._writeRawData(entry.name + '.pyc', data)

            else:
                self._writeRawData(entry.name, data)

                if entry.typeCmprsData == b'z' or entry.typeCmprsData == b'Z':
                    self._extractPyz(entry.name)

    def _writePyc(self, filename, data):
        with open(filename, 'wb') as pycFile:
            pycFile.write(pyc_magic)            # pyc magic

            if self.pyver >= 37:                # PEP 552 -- Deterministic pycs
                pycFile.write(b'\0' * 4)        # Bitfield
                pycFile.write(b'\0' * 8)        # (Timestamp + size) || hash 

            else:
                pycFile.write(b'\0' * 4)      # Timestamp
                if self.pyver >= 33:
                    pycFile.write(b'\0' * 4)  # Size parameter added in Python 3.3

            pycFile.write(data)

    def _extractPyz(self, name):
        dirName =  name + '_extracted'
        # Create a directory for the contents of the pyz
        if not os.path.exists(dirName):
            os.mkdir(dirName)

        with open(name, 'rb') as f:
            pyzMagic = f.read(4)
            assert pyzMagic == b'PYZ\0' # Sanity Check

            pycHeader = f.read(4) # Python magic value

            # Skip PYZ extraction if not running under the same python version
            if pyc_magic != pycHeader:
                print('[!] Warning: This script is running in a different Python version than the one used to build the executable.')
                print('[!] Please run this script in Python{0} to prevent extraction errors during unmarshalling'.format(self.pyver))
                print('[!] Skipping pyz extraction')
                return

            (tocPosition, ) = struct.unpack('!i', f.read(4))
            f.seek(tocPosition, os.SEEK_SET)

            try:
                toc = marshal.load(f)
            except:
                print('[!] Unmarshalling FAILED. Cannot extract {0}. Extracting remaining files.'.format(name))
                return

            print('[+] Found {0} files in PYZ archive'.format(len(toc)))

            # From pyinstaller 3.1+ toc is a list of tuples
            if type(toc) == list:
                toc = dict(toc)

            for key in toc.keys():
                (ispkg, pos, length) = toc[key]
                f.seek(pos, os.SEEK_SET)
                fileName = key

                try:
                    # for Python > 3.3 some keys are bytes object some are str object
                    fileName = fileName.decode('utf-8')
                except:
                    pass

                # Prevent writing outside dirName
                fileName = fileName.replace('..', '__').replace('.', os.path.sep)

                if ispkg == 1:
                    filePath = os.path.join(dirName, fileName, '__init__.pyc')

                else:
                    filePath = os.path.join(dirName, fileName + '.pyc')

                fileDir = os.path.dirname(filePath)
                if not os.path.exists(fileDir):
                    os.makedirs(fileDir)

                try:
                    data = f.read(length)
                    data = zlib.decompress(data)
                except:
                    print('[!] Error: Failed to decompress {0}, probably encrypted. Extracting as is.'.format(filePath))
                    open(filePath + '.encrypted', 'wb').write(data)
                else:
                    self._writePyc(filePath, data)

def main(exe_file):
    arch = PyInstArchive(exe_file)
    if arch.open():
        if arch.checkFile():
            if arch.getCArchiveInfo():
                arch.parseTOC()
                arch.extractFiles()
                arch.close()
                print('[*] Successfully extracted pyinstaller archive: {0}'.format(exe_file))
                return

        arch.close()

#---------------------------------------------------------------

#BY LAW

def end():
    shutil.rmtree("Process")

def uncompyle(c):
    os.system("decompyle3 -o result/source_code.py " + "./Process/" + c)
    end()

def checking(a):
    if os.path.exists("Process"):
        shutil.rmtree("Process")
    if os.path.exists(a):
        shutil.rmtree(a)

def starting():
    directory = os.getcwd()
    print(directory)

    file = sys.argv[1]
    os.chdir(f'{directory}')
    folder_location = r"./" + file + "_extracted/"
    print(Fore.LIGHTRED_EX + "\n[>] Pyinstaller Extraction...\n" + Fore.RESET)

    checking(folder_location)

    if not os.path.exists("Process"):
        os.makedirs("Process")

    main(file)
    os.chdir(f'{directory}')

    fileExt = r".manifest"
    manifests = [_ for _ in os.listdir(folder_location) if _.endswith(fileExt)]
    manifests = [ x for x in manifests if "pyi-windows-manifest-filename" not in x ]
    manifests = ''.join(manifests)
    file_pyc1 = manifests.replace('.manifest', '.pyc')
    file_pyc2 = manifests.replace('.manifest', '.pyo')

    if os.path.exists(folder_location + file_pyc1):
        shutil.copy(folder_location + file_pyc1, "Process")
        uncompyle(file_pyc1)

    elif os.path.exists(folder_location + file_pyc2):
        shutil.copy(folder_location + file_pyc2, "Process")
        uncompyle(file_pyc2)

    else:
        print(Fore.LIGHTRED_EX + "[!] No entry point found!" + Fore.RESET)
        end()

if __name__ == "__main__":
    app = PyInstallerExtractorApp()
    app.mainloop()