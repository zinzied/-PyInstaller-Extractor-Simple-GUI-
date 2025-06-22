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
import tkinter as tk
from tkinterdnd2 import DND_FILES, TkinterDnD
import threading
import time

class PyInstallerExtractorApp(TkinterDnD.Tk):
    def __init__(self):
        super().__init__()
        self.title("PyInstaller Extractor - Enhanced")
        self.geometry("600x450")
        self.resizable(True, True)

        # Configure the window
        self.configure(bg='#2b2b2b')

        # Variables
        self.current_file = None
        self.extraction_thread = None

        self.setup_ui()
        self.setup_drag_drop()

    def setup_ui(self):
        # Main frame
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Title
        title_label = ctk.CTkLabel(main_frame, text="PyInstaller Extractor",
                                  font=ctk.CTkFont(size=24, weight="bold"))
        title_label.pack(pady=(20, 10))

        # Drag and drop area
        self.drop_frame = ctk.CTkFrame(main_frame, height=100, corner_radius=10)
        self.drop_frame.pack(fill="x", padx=20, pady=10)
        self.drop_frame.pack_propagate(False)

        self.drop_label = ctk.CTkLabel(self.drop_frame,
                                      text="Drag & Drop executable file here\nor click Browse to select",
                                      font=ctk.CTkFont(size=14))
        self.drop_label.pack(expand=True)

        # File info frame
        self.info_frame = ctk.CTkFrame(main_frame)
        self.info_frame.pack(fill="x", padx=20, pady=10)

        self.file_label = ctk.CTkLabel(self.info_frame, text="No file selected",
                                      font=ctk.CTkFont(size=12))
        self.file_label.pack(pady=10)

        # Buttons frame
        button_frame = ctk.CTkFrame(main_frame)
        button_frame.pack(fill="x", padx=20, pady=10)

        self.browse_button = ctk.CTkButton(button_frame, text="Browse",
                                          command=self.browse_file, width=120)
        self.browse_button.pack(side="left", padx=(10, 5), pady=10)

        self.extract_button = ctk.CTkButton(button_frame, text="Extract",
                                           command=self.start_extraction,
                                           width=120, state="disabled")
        self.extract_button.pack(side="left", padx=5, pady=10)

        self.clear_button = ctk.CTkButton(button_frame, text="Clear",
                                         command=self.clear_selection, width=120)
        self.clear_button.pack(side="right", padx=(5, 10), pady=10)

        # Progress frame
        progress_frame = ctk.CTkFrame(main_frame)
        progress_frame.pack(fill="x", padx=20, pady=10)

        self.status_label = ctk.CTkLabel(progress_frame, text="Ready",
                                        font=ctk.CTkFont(size=12))
        self.status_label.pack(pady=(10, 5))

        self.progress_bar = ctk.CTkProgressBar(progress_frame, width=400)
        self.progress_bar.pack(pady=(0, 10), padx=20)
        self.progress_bar.set(0)

        # Log frame
        log_frame = ctk.CTkFrame(main_frame)
        log_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        log_title = ctk.CTkLabel(log_frame, text="Extraction Log",
                                font=ctk.CTkFont(size=14, weight="bold"))
        log_title.pack(pady=(10, 5))

        # Create a text widget for logs
        self.log_text = tk.Text(log_frame, height=8, bg='#1a1a1a', fg='#ffffff',
                               font=('Consolas', 10), wrap=tk.WORD)
        self.log_text.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # Scrollbar for log
        scrollbar = tk.Scrollbar(self.log_text)
        scrollbar.pack(side="right", fill="y")
        self.log_text.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.log_text.yview)

    def setup_drag_drop(self):
        """Setup drag and drop functionality"""
        self.drop_target_register(DND_FILES)
        self.dnd_bind('<<Drop>>', self.on_drop)

        # Make the drop frame accept drops
        self.drop_frame.drop_target_register(DND_FILES)
        self.drop_frame.dnd_bind('<<Drop>>', self.on_drop)

    def on_drop(self, event):
        """Handle dropped files"""
        files = self.tk.splitlist(event.data)
        if files:
            file_path = files[0]  # Take the first file
            if file_path.lower().endswith('.exe'):
                self.set_file(file_path)
            else:
                self.log_message("Error: Please drop an executable (.exe) file")

    def browse_file(self):
        """Browse for file using file dialog"""
        file_path = filedialog.askopenfilename(
            title="Select an executable file",
            filetypes=[("Executable files", "*.exe"), ("All files", "*.*")]
        )
        if file_path:
            self.set_file(file_path)

    def set_file(self, file_path):
        """Set the selected file and update UI"""
        self.current_file = file_path
        filename = os.path.basename(file_path)
        file_size = os.path.getsize(file_path)
        size_mb = file_size / (1024 * 1024)

        self.file_label.configure(text=f"File: {filename}\nSize: {size_mb:.2f} MB")
        self.extract_button.configure(state="normal")
        self.log_message(f"Selected file: {filename}")

    def clear_selection(self):
        """Clear the current file selection"""
        self.current_file = None
        self.file_label.configure(text="No file selected")
        self.extract_button.configure(state="disabled")
        self.progress_bar.set(0)
        self.status_label.configure(text="Ready")
        self.log_text.delete(1.0, tk.END)

    def log_message(self, message):
        """Add a message to the log"""
        timestamp = time.strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        self.update()

    def update_progress(self, value, status=""):
        """Update progress bar and status"""
        self.progress_bar.set(value)
        if status:
            self.status_label.configure(text=status)
        self.update()

    def start_extraction(self):
        """Start extraction in a separate thread"""
        if not self.current_file:
            return

        self.extract_button.configure(state="disabled")
        self.browse_button.configure(state="disabled")
        self.clear_button.configure(state="disabled")

        # Start extraction in a separate thread
        self.extraction_thread = threading.Thread(target=self.extract_file_threaded)
        self.extraction_thread.daemon = True
        self.extraction_thread.start()

    def extract_file_threaded(self):
        """Extract file in a separate thread with progress updates"""
        try:
            self.update_progress(0.1, "Initializing extraction...")
            self.log_message("Starting extraction process...")

            # Create enhanced archive object that supports progress callbacks
            arch = EnhancedPyInstArchive(self.current_file, self)

            if arch.open():
                self.update_progress(0.2, "Checking file format...")
                if arch.checkFile():
                    self.update_progress(0.3, "Reading archive information...")
                    if arch.getCArchiveInfo():
                        self.update_progress(0.4, "Parsing table of contents...")
                        arch.parseTOC()
                        self.update_progress(0.5, "Extracting files...")
                        arch.extractFiles()
                        arch.close()
                        self.update_progress(1.0, "Extraction completed successfully!")
                        self.log_message("Extraction completed successfully!")
                        messagebox.showinfo("Success", "Extraction completed successfully!")
                        return
                arch.close()

            self.update_progress(0, "Extraction failed")
            self.log_message("Extraction failed!")
            messagebox.showerror("Error", "Extraction failed!")

        except Exception as e:
            self.update_progress(0, "Error occurred")
            self.log_message(f"Error: {str(e)}")
            messagebox.showerror("Error", f"An error occurred: {e}")
        finally:
            # Re-enable buttons
            self.extract_button.configure(state="normal")
            self.browse_button.configure(state="normal")
            self.clear_button.configure(state="normal")

init()
# imp is deprecated in Python3 in favour of importlib
if sys.version_info.major == 3:
    from importlib.util import MAGIC_NUMBER
    pyc_magic = MAGIC_NUMBER

# The rest of your code remains unchanged

class EnhancedPyInstArchive:
    """Enhanced PyInstaller Archive class with progress callback support"""

    def __init__(self, path, gui_callback=None):
        self.archive = PyInstArchive(path)
        self.gui = gui_callback

    def open(self):
        return self.archive.open()

    def close(self):
        return self.archive.close()

    def checkFile(self):
        result = self.archive.checkFile()
        if self.gui:
            if result:
                version = "2.0" if self.archive.pyinstVer == 20 else "2.1+"
                self.gui.log_message(f"Detected PyInstaller version: {version}")
            else:
                self.gui.log_message("Not a valid PyInstaller archive")
        return result

    def getCArchiveInfo(self):
        result = self.archive.getCArchiveInfo()
        if self.gui and result:
            self.gui.log_message(f"Python version: {self.archive.pyver}")
            self.gui.log_message(f"Package size: {self.archive.overlaySize} bytes")
        return result

    def parseTOC(self):
        self.archive.parseTOC()
        if self.gui:
            self.gui.log_message(f"Found {len(self.archive.tocList)} files in archive")

    def extractFiles(self):
        if not hasattr(self.archive, 'tocList'):
            return

        total_files = len(self.archive.tocList)
        if self.gui:
            self.gui.log_message(f"Extracting {total_files} files...")

        # Create extraction directory
        extractionDir = os.path.join(os.getcwd(), os.path.basename(self.archive.filePath) + '_extracted')
        if not os.path.exists(extractionDir):
            os.mkdir(extractionDir)

        original_dir = os.getcwd()
        os.chdir(extractionDir)

        try:
            for i, entry in enumerate(self.archive.tocList):
                # Update progress
                progress = 0.5 + (i / total_files) * 0.5  # 50% to 100%
                if self.gui:
                    self.gui.update_progress(progress, f"Extracting: {entry.name}")

                # Extract the file (using original logic)
                basePath = os.path.dirname(entry.name)
                if basePath != '':
                    if not os.path.exists(basePath):
                        os.makedirs(basePath)

                self.archive.fPtr.seek(entry.position, os.SEEK_SET)
                data = self.archive.fPtr.read(entry.cmprsdDataSize)

                if entry.cmprsFlag == 1:
                    data = zlib.decompress(data)

                if entry.typeCmprsData == b's':
                    if self.gui:
                        self.gui.log_message(f"Found entry point: {entry.name}.pyc")
                    self.archive._writePyc(entry.name + '.pyc', data)
                elif entry.typeCmprsData == b'M' or entry.typeCmprsData == b'm':
                    self.archive._writeRawData(entry.name + '.pyc', data)
                else:
                    self.archive._writeRawData(entry.name, data)
                    if entry.typeCmprsData == b'z' or entry.typeCmprsData == b'Z':
                        self.archive._extractPyz(entry.name)

        finally:
            os.chdir(original_dir)

        if self.gui:
            self.gui.log_message(f"Files extracted to: {extractionDir}")

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