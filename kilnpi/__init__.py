
import socket

def get_ipaddress()->str:
  '''Get ip address of self.

  This is a bit hacky and relies on Internet service, which is OK since
  we're using it to figure out where on the Internet this thing is.
  '''
  ipaddr = None
  try:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    ipaddr = s.getsockname()[0]
    s.close()
  except Exception as e:
    print(e)
  return ipaddr


