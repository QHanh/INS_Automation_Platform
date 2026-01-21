import json
import urllib.request
import time
import jwt
import hashlib
from getmac import get_mac_address

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
    """Lấy thời gian chuẩn (Unix Timestamp) qua HTTP API thay vì NTP."""
    # Danh sách các API thời gian phổ biến (HTTP 80/443 hiếm khi bị chặn)
    time_apis = [
        "http://worldtimeapi.org/api/timezone/Etc/UTC",
        "https://timeapi.io/api/Time/current/zone?timeZone=UTC"
    ]
    
    for url in time_apis:
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=5) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode())
                    if 'unixtime' in data:
                        return data['unixtime']
        except Exception as e:
            print(f"⚠️ Failed to fetch time from {url}: {e}")
            continue

    # Fallback cuối cùng: Lấy từ Header của Google (vô cùng tin cậy)
    try:
        with urllib.request.urlopen("http://www.google.com", timeout=5) as response:
            date_str = response.headers['Date']
            # Convert 'Wed, 21 Jan 2026 07:10:00 GMT' to unix timestamp
            struct_time = time.strptime(date_str, '%a, %d %b %Y %H:%M:%S %Z')
            return int(time.mktime(struct_time))
    except Exception as e:
        print(f"⚠️ Failed to fetch time from Google headers: {e}")
            
    return None

def verify_license_token(token: str) -> dict:
    current_time = get_network_time()
    
    if current_time is None:
        # Nếu không lấy được giờ từ mạng, có thể log lại nhưng để đảm bảo license không bị hack 
        # bằng cách chỉnh giờ máy, chúng ta nên bắt buộc có giờ mạng.
        raise ValueError("Không thể kết nối Internet để xác thực thời gian. Vui lòng kiểm tra kết nối mạng (Cổng 443/80).")
    
    print("✅ Thời gian mạng (UTC):", current_time)
    
    # Chuyển đổi sang giờ Việt Nam (UTC+7) để bạn dễ theo dõi trong log
    vn_time = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(current_time + 7 * 3600))
    print(f"🕒 Giờ xác thực (Vietnam Time): {vn_time}")

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
    local_hash = hash_machine_id(mac)
    if local_hash != payload.get("machine"):
        raise ValueError("License không khớp với máy.")

    return payload

if __name__ == "__main__":
    try:
        # Test logic
        current = get_network_time()
        print(f"Current Network Time: {current}")
    except Exception as ex:
        print("❌ Lỗi:", ex)