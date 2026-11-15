"""Windows credential-store access for the website moderator, unrelated to wallets."""
import ctypes
from ctypes import wintypes
import os
import secrets

TARGET = "ObsoleteCoin/ForumAdmin"
URL = "https://obsoletecoin.pages.dev/forum/admin"

class Credential(ctypes.Structure):
    _fields_ = [
        ("Flags", wintypes.DWORD), ("Type", wintypes.DWORD),
        ("TargetName", wintypes.LPWSTR), ("Comment", wintypes.LPWSTR),
        ("LastWritten", wintypes.FILETIME), ("CredentialBlobSize", wintypes.DWORD),
        ("CredentialBlob", ctypes.POINTER(ctypes.c_ubyte)),
        ("Persist", wintypes.DWORD), ("AttributeCount", wintypes.DWORD),
        ("Attributes", ctypes.c_void_p), ("TargetAlias", wintypes.LPWSTR),
        ("UserName", wintypes.LPWSTR),
    ]

def api():
    if os.name != "nt":
        raise RuntimeError("Windows Credential Manager is required.")
    lib = ctypes.WinDLL("Advapi32.dll", use_last_error=True)
    lib.CredReadW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, ctypes.POINTER(ctypes.POINTER(Credential))]
    lib.CredReadW.restype = wintypes.BOOL
    lib.CredWriteW.argtypes = [ctypes.POINTER(Credential), wintypes.DWORD]
    lib.CredWriteW.restype = wintypes.BOOL
    lib.CredFree.argtypes = [ctypes.c_void_p]
    return lib

def read_password(target=TARGET):
    lib = api()
    ptr = ctypes.POINTER(Credential)()
    if not lib.CredReadW(target, 1, 0, ctypes.byref(ptr)):
        if ctypes.get_last_error() == 1168:
            return None
        raise RuntimeError("Credential store could not be read.")
    try:
        return ctypes.string_at(ptr.contents.CredentialBlob, ptr.contents.CredentialBlobSize).decode("utf-16-le")
    finally:
        lib.CredFree(ptr)

def create_password():
    existing = read_password()
    if existing is not None:
        if len(existing) != 43:
            raise RuntimeError("Unexpected existing credential; refusing to replace it.")
        return existing
    password = secrets.token_urlsafe(32)
    blob = password.encode("utf-16-le")
    data = (ctypes.c_ubyte * len(blob)).from_buffer_copy(blob)
    item = Credential()
    item.Type = 1
    item.TargetName = TARGET
    item.Comment = "Obsolete Coin website moderator password. Not a wallet key."
    item.CredentialBlobSize = len(blob)
    item.CredentialBlob = ctypes.cast(data, ctypes.POINTER(ctypes.c_ubyte))
    item.Persist = 2
    item.UserName = "admin"
    if not api().CredWriteW(ctypes.byref(item), 0):
        raise RuntimeError("Credential store write failed.")
    if read_password() != password:
        raise RuntimeError("Credential verification failed.")
    return password

def show():
    import tkinter as tk
    from tkinter import messagebox
    import webbrowser
    root = tk.Tk()
    root.title("Obsolete Coin - Forum administrator")
    root.geometry("620x240")
    root.resizable(False, False)
    password = read_password()
    if password is None:
        root.withdraw()
        messagebox.showerror("Obsolete Coin", "No forum administrator credential is stored for this Windows account.")
        root.destroy()
        return
    tk.Label(root, text="Forum administrator password", font=("Arial", 15, "bold")).pack(pady=(18, 8))
    entry = tk.Entry(root, width=52, font=("Consolas", 12), show="*")
    entry.insert(0, password)
    entry.configure(state="readonly")
    entry.pack(padx=15, pady=8)
    status = tk.StringVar(value="Stored in Windows Credential Manager for this Windows account.")
    def copy():
        root.clipboard_clear()
        root.clipboard_append(password)
        root.update()
        status.set("Copied. Paste it into the administrator sign-in form.")
    buttons = tk.Frame(root)
    buttons.pack(pady=10)
    tk.Button(buttons, text="Copy password", command=copy).pack(side="left", padx=6)
    tk.Button(buttons, text="Show / hide", command=lambda: entry.configure(show="" if entry.cget("show") else "*")).pack(side="left", padx=6)
    tk.Button(buttons, text="Open admin panel", command=lambda: webbrowser.open(URL)).pack(side="left", padx=6)
    tk.Label(root, textvariable=status, wraplength=580).pack(pady=4)
    tk.Label(root, text="Keep this password private. It is unrelated to your wallet.", wraplength=580).pack()
    root.mainloop()

if __name__ == "__main__":
    show()
