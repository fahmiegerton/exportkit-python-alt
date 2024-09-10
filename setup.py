import sys
from cx_Freeze import setup, Executable
import os
import tkinterdnd2

tkdnd_path = os.path.join(os.path.dirname(tkinterdnd2.__file__), 'tkdnd')

build_exe_options = {
	"packages": ["os", "tkinter", "tkinterdnd2", "psd_tools"],
	"include_files": [(tkdnd_path, "tkdnd")],
}

base = None
if sys.platform == "win32":
	base = "Win32GUI"

setup(
	name="PSDConverter",
	version="0.1",
	description="PSD to JSON Converter",
	options={"build_exe": build_exe_options},
	executables=[Executable("main.py", base=base)]
)