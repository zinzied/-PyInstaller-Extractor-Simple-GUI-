# PyInstaller Extractor - Enhanced GUI

A powerful and user-friendly GUI tool for extracting and decompiling PyInstaller executables with enhanced features including progress tracking and drag & drop support.

![image](https://github.com/user-attachments/assets/196b265f-eccd-437c-9661-fd39fcf2d252)

## ✨ New Features

### 🎯 Progress Bar & Status Updates
- Real-time progress tracking during extraction
- Detailed status messages for each extraction phase
- Visual feedback for long-running operations

### 🖱️ Drag & Drop Support
- Simply drag and drop executable files onto the application
- Automatic file validation (only .exe files accepted)
- Intuitive user interface

### 📊 Enhanced User Interface
- Modern CustomTkinter-based GUI
- Resizable window with responsive layout
- File information display (name, size)
- Real-time extraction log with timestamps
- Clear and intuitive button layout

### 🔧 Additional Improvements
- Threaded extraction to prevent UI freezing
- Better error handling and user feedback
- Detailed logging of extraction process
- File selection validation
- Clean and professional interface

## 🚀 Features

- **PyInstaller Archive Extraction**: Supports PyInstaller versions 2.0 and 2.1+
- **Automatic Decompilation**: Uses decompyle3 for Python bytecode decompilation
- **Progress Tracking**: Real-time progress bar and status updates
- **Drag & Drop**: Intuitive file selection via drag and drop
- **Detailed Logging**: Comprehensive extraction log with timestamps
- **Error Handling**: Robust error handling with user-friendly messages
- **Modern GUI**: Clean and responsive user interface

## 📋 Requirements

- Python 3.6+
- CustomTkinter
- tkinterdnd2
- colorama
- pyinstaller
- decompyle3 (for decompilation)

## 🛠️ Installation

1. Clone this repository:
```bash
git clone https://github.com/yourusername/PyInstaller-Extractor-Enhanced-GUI.git
cd PyInstaller-Extractor-Enhanced-GUI
```

2. Install required dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
python main.py
```

## 📖 Usage

### Method 1: Drag & Drop
1. Launch the application
2. Drag an executable (.exe) file onto the drop area
3. Click "Extract" to begin the extraction process
4. Monitor progress in the progress bar and log area

### Method 2: File Browser
1. Launch the application
2. Click "Browse" to select an executable file
3. Choose your target .exe file
4. Click "Extract" to begin the extraction process

### Output
- Extracted files will be saved in a folder named `[filename]_extracted`
- The log will show detailed information about the extraction process
- Entry points and important files will be highlighted in the log

## 🎮 Interface Guide

- **Drop Area**: Drag and drop executable files here
- **File Info**: Shows selected file name and size
- **Browse Button**: Open file dialog to select files
- **Extract Button**: Start the extraction process (enabled after file selection)
- **Clear Button**: Clear current selection and reset the interface
- **Progress Bar**: Shows extraction progress (0-100%)
- **Status Label**: Current operation status
- **Log Area**: Detailed extraction log with timestamps

## 🔍 Supported File Types

- PyInstaller executables (.exe)
- Versions 2.0 and 2.1+ supported
- Automatic version detection

## ⚠️ Notes

- The application requires the same Python version as the target executable for optimal decompilation
- Some encrypted or obfuscated executables may not extract completely
- Large executables may take several minutes to process

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.
