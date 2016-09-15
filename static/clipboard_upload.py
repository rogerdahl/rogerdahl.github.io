'''
Upload data in clipboard to web site and replace clipboard with paths.

Supports:
 - Files
 - Image data
 - Text
 
Example usage:
 - Select a couple of files in Explorer and Copy.
 - Run the script.
 - Paste the URLs into an email.
'''

# Std
import sys
import os
import time
import StringIO
import uuid

# Python Image Library
import Image
import ImageGrab

# Paramiko SFTP client
import paramiko

# Win
import win32api
import win32con
import win32clipboard
import ctypes

GlobalLock = ctypes.windll.kernel32.GlobalLock
GlobalAlloc = ctypes.windll.kernel32.GlobalAlloc
GlobalUnlock = ctypes.windll.kernel32.GlobalUnlock
memcpy = ctypes.cdll.msvcrt.memcpy

# Config.

# The drop folder as seen from the web.
remote_root_http = 'http://my.server.com/upload/'

# The drop folder as seen from the user account.
remote_root_path = '/var/www/upload/'

# SSH server and account.
host = "my.server.com"
username = "myusername"
password = "mypassword"
port = 22

# The file format to use for generated image files.
image_file_type = 'png'

# End config.

class NoUpload(Exception):
  pass

def upload_clipboard_image():
  im = ImageGrab.grabclipboard()

  if not isinstance(im, Image.Image):
    raise NoUpload

  print 'Uploading clipboard image'

  f = StringIO.StringIO()
  im.save(f, image_file_type)
  data = f.getvalue()

  # Generate remote path
  
  remote_name = str(uuid.uuid1()) + '.' + image_file_type
  remote_abs_path = remote_root_path + remote_name

  # Upload file with paramiko sftp
  transport = paramiko.Transport((host, port))
  transport.connect(username=username, password=password)
  sftp = paramiko.SFTPClient.from_transport(transport)
  fr = sftp.file(remote_abs_path, 'wb')
  fr.set_pipelined(True)
  fr.write(data)
  fr.close()  
  sftp.close()
  transport.close()

  return [remote_name]

def upload_text():
  clip = win32clipboard.OpenClipboard(0)

  try:  
    text = win32clipboard.GetClipboardData(win32con.CF_TEXT)
  except TypeError:
    win32clipboard.CloseClipboard()
    raise NoUpload

  print 'Uploading clipboard text'

  # Generate remote path
  remote_name = str(uuid.uuid1()) + '.txt'
  remote_abs_path = remote_root_path + remote_name

  # Upload file with paramiko sftp
  transport = paramiko.Transport((host, port))
  transport.connect(username=username, password=password)
  sftp = paramiko.SFTPClient.from_transport(transport)
  fr = sftp.file(remote_abs_path, 'wb')
  fr.set_pipelined(True)
  fr.write(text)
  fr.close()  
  sftp.close()
  transport.close()

  win32clipboard.CloseClipboard()

  return [remote_name]

def upload_files():
  clip = win32clipboard.OpenClipboard(0)

  try:  
    local_paths = win32clipboard.GetClipboardData(win32con.CF_HDROP)
  except TypeError:
    win32clipboard.CloseClipboard()
    raise NoUpload

  transport = paramiko.Transport((host, port))
  transport.connect(username=username, password=password)
  sftp = paramiko.SFTPClient.from_transport(transport)

  remote_names = []
  for local_path in local_paths:
    print 'Uploading: {0}'.format(local_path)
    
    # Generate remote path
    remote_name = os.path.basename(local_path)
    remote_abs_path = remote_root_path + remote_name
    sftp.put(local_path, remote_abs_path)
    remote_names.append(remote_name)
  sftp.close()
  transport.close()
  
  win32clipboard.CloseClipboard()

  return remote_names

def set_clipboard_text(text):
  buffer = ctypes.create_string_buffer(text)
  bufferSize = ctypes.sizeof(buffer)
  hGlobalMem = GlobalAlloc(ctypes.c_int(win32con.GHND), ctypes.c_int(bufferSize))
  GlobalLock.restype = ctypes.c_void_p
  lpGlobalMem = GlobalLock(ctypes.c_int(hGlobalMem))
  memcpy(lpGlobalMem, ctypes.addressof(buffer), ctypes.c_int(bufferSize))
  GlobalUnlock(ctypes.c_int(hGlobalMem))
  win32clipboard.OpenClipboard(0)
  win32clipboard.EmptyClipboard()
  win32clipboard.SetClipboardData(win32con.CF_TEXT, hGlobalMem)
  win32clipboard.CloseClipboard()

def set_clipboard_paths(files):
  html_paths = [remote_root_http + f for f in files]
  text = '\r\n'.join(html_paths) + '\r\n'
  print 'Copied to clipboard:\n{0}'.format(text)
  set_clipboard_text(text)
  
def main():
  try:
    files = upload_files()
  except NoUpload:
    pass
  else:
    set_clipboard_paths(files)
    exit()

  try:
    files = upload_clipboard_image()
  except NoUpload:
    pass
  else:
    set_clipboard_paths(files)
    exit()

  try:
    files = upload_text()
  except NoUpload:
    pass
  else:
    set_clipboard_paths(files)
    exit()

  print 'Nothing uploaded'
  
if __name__ == "__main__":
  main()  
