import jwt
import hashlib
from getmac import get_mac_address
import socket
import struct

PUBLIC_KEY = """-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAv3ibdeBYtYS/VEWkkLmx
N1CsP9K+LS+qJuQme+vEZqcxgYni7krai9ndDs0IRt/QGEp2WZTMTqKi8Li60fX3
UXcesMvKqdJWjKtc0mXijSIpzhHJ+GPws/xZB+Ud4JQBSeLgc62g2QwRdBPHAVEe
4eKTD991dSq3gaWXTT8QVSRJvfKoW7ORyh7uyJf9WvFCmi4x7BHBaYTB9oci47ls
iTFo84KOpWUvFQ/JTUoOxn+3v+tVPV0tcaC1gqEsVK1S2+jijGLXWGe5wE9jMW2/
hCLbkR14/kkR3Z4772YPPY5vstGwSx/hLjBTM5dr+iB5WC0UG1ie4nr/G+uoYdiW
NQIDAQAB
-----END PUBLIC KEY-----"""

def hash_machine_id(mac: str) -> str:
    return hashlib.sha256(mac.strip().lower().encode('utf-8')).hexdigest()

def get_network_time():
    NTP_SERVER = "pool.ntp.org"
    NTP_DELTA = 2208988800 
    
    NTP_QUERY = bytearray(48)
    NTP_QUERY[0] = 0x1b
    
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.settimeout(5) 
            s.sendto(NTP_QUERY, (NTP_SERVER, 123))
            data, address = s.recvfrom(1024)
            
        unpacked = struct.unpack('!12I', data)
        t = unpacked[10] - NTP_DELTA
        return t
    except Exception:
        return None

def verify_license_token(token: str) -> dict:
    current_time = get_network_time()
    
    if current_time is None:
        raise ValueError("Không thể kết nối Internet để xác thực thời gian. Vui lòng kiểm tra kết nối mạng.")
    
    print("✅ Thời gian mạng:", current_time)

    try:
        payload = jwt.decode(
            token,
            PUBLIC_KEY,
            algorithms=["RS256"],
            options={"require": ["exp", "nbf", "iat"], "verify_exp": False}
        )
        
        exp = payload.get("exp")
        if current_time > exp:
             raise jwt.ExpiredSignatureError("License đã hết hạn (Network Time Check).")
             
    except jwt.ExpiredSignatureError:
        raise ValueError("License đã hết hạn.")
    except jwt.InvalidSignatureError:
        raise ValueError("Signature không hợp lệ. License bị sửa đổi.")
    except Exception as e:
        raise ValueError(f"License không hợp lệ: {e}")

    mac = get_mac_address(network_request=True)
    # print(mac)
    local_hash = hash_machine_id(mac)
    if local_hash != payload.get("machine"):
        raise ValueError("License không khớp với máy.")

    return payload

if __name__ == "__main__":
    try:
        token = open("./LICENSEs/license_hqha.lic").read().strip()
        payload = verify_license_token(token)
        print("✅ License hợp lệ:", payload)
    except FileNotFoundError:
        print("❌ Không tìm thấy file license.lic")
    except Exception as ex:
        print("❌ Lỗi license:", ex)