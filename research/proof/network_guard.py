"""Reject private destinations for discovered URLs and browser HTTP requests."""
import ipaddress,socket
from urllib.parse import urlsplit

def public_url(url):
 try:
  u=urlsplit(url)
  if u.scheme not in ('http','https') or u.username or u.password or not u.hostname or u.port not in (None,80,443):return False
  if u.hostname.lower()=='localhost' or u.hostname.lower().endswith(('.local','.localhost')):return False
  addresses=socket.getaddrinfo(u.hostname,u.port or (443 if u.scheme=='https' else 80),type=socket.SOCK_STREAM)
  return bool(addresses) and all(ipaddress.ip_address(a[4][0]).is_global for a in addresses)
 except (ValueError,OSError):return False
