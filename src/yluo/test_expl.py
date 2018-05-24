import ctypes

ctypes.windll.ole32.CoInitialize(None)
upath = r"D:\Code\code.7z"
pidl = ctypes.windll.shell32.ILCreateFromPathW(upath)
ctypes.windll.shell32.SHOpenFolderAndSelectItems(pidl, 0, None, 0)
ctypes.windll.shell32.ILFree(pidl)
ctypes.windll.ole32.CoUninitialize()
