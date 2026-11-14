"""Unpack the official Tcl/Tk script ZIPs for explicit build/runtime discovery."""
import json,os,sys,zipfile
from pathlib import Path
base=Path(sys.base_prefix)/'tcl';dest=Path('.local/tk-scripts').resolve();dest.mkdir(parents=True,exist_ok=True)
result={}
for name,folder,variable in [('libtcl9.0.4.zip','tcl_library','TCL_LIBRARY'),('libtk9.0.4.zip','tk_library','TK_LIBRARY')]:
 archive=base/name
 if archive.is_file():
  with zipfile.ZipFile(archive) as z:
   for entry in z.infolist():
    target=(dest/entry.filename).resolve()
    if not target.is_relative_to(dest):raise ValueError('Archive path outside build directory')
    if entry.is_dir():target.mkdir(parents=True,exist_ok=True)
    else:target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(z.read(entry))
  result[variable]=str(dest/folder)
  os.environ[variable]=result[variable]
import tkinter
root=tkinter.Tk();root.withdraw();assert root.tk.eval('info patchlevel')=='9.0.4';root.destroy()
print(json.dumps(result))
