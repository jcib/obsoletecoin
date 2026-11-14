"""Render and check the real Tk desktop (xvfb-run on headless Linux)."""
import argparse, tkinter as tk
from pathlib import Path
from wallet import Wallet
from rpc import RPC
p=argparse.ArgumentParser();p.add_argument('--screenshot',type=Path);args=p.parse_args()
import sys
if sys.platform=='win32':
    import ctypes
    ctypes.windll.user32.SetProcessDPIAware()
root=tk.Tk();root.geometry('900x650+20+20')
app=Wallet(root,RPC(Path('unused-demo-cookie')),demo=True)
errors=[]
root.report_callback_exception=lambda *error:errors.append(error)
root.update()
assert app.balance.get()=='12,345.00000000 OBSC'
assert len(app.table.get_children())==2
assert 'DEMO' in app.status.get()
assert root.winfo_width()>=740
if args.screenshot:
    import sys,subprocess
    args.screenshot.parent.mkdir(parents=True,exist_ok=True)
    if sys.platform=='win32':
        root.attributes('-topmost',True);root.update()
        x,y,w,h=root.winfo_rootx(),root.winfo_rooty(),root.winfo_width(),root.winfo_height()
        script="""Add-Type -TypeDefinition 'using System.Runtime.InteropServices; public class Dpi { [DllImport("user32.dll")] public static extern bool SetProcessDPIAware(); }'
[Dpi]::SetProcessDPIAware() | Out-Null
Add-Type -AssemblyName System.Drawing
$bmp = New-Object System.Drawing.Bitmap(%d,%d)
$g = [System.Drawing.Graphics]::FromImage($bmp)
$g.CopyFromScreen(%d,%d,0,0,$bmp.Size)
$bmp.Save(TARGET,[System.Drawing.Imaging.ImageFormat]::Png)
$g.Dispose()
$bmp.Dispose()
"""%(w,h,x,y)
        target=str(args.screenshot.resolve()).replace("'","''")
        script=script.replace('TARGET',"'"+target+"'")
        subprocess.run(['powershell','-NoProfile','-Command',script],check=True)
    else:
        from PIL import ImageGrab
        ImageGrab.grab(bbox=(root.winfo_rootx(),root.winfo_rooty(),root.winfo_rootx()+root.winfo_width(),root.winfo_rooty()+root.winfo_height())).save(args.screenshot)
root.destroy()
assert not errors,errors
print('Tk wallet rendered successfully; no callback errors')
