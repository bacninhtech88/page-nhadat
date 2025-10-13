# ====================================================================
# FILE: facebook_tools.py - Xử lý Graph API và Webhook Logic
# ====================================================================
import requests
import os
import logging 
from dotenv import load_dotenv


# Thiết lập logging
logger = logging.getLogger(__name__)

# ====================================================================
# 1. GRAPH API TOOLS (Các hàm gọi API Facebook)
# ====================================================================

# Cần truyền access_token và page_id vào hàm
def get_page_info(page_id: str, access_token: str) -> dict:
    """Lấy thông tin Page cụ thể bằng ID và Access Token (Cần truyền từ main.py)."""
    url = f"https://graph.facebook.com/v19.0/{page_id}"
    params = {
        "access_token": access_token, # SỬ DỤNG tham số access_token
        "fields": "name,fan_count,about"
    }
    try:
        res = requests.get(url, params=params, timeout=5)
        res.raise_for_status() # Báo lỗi nếu status code không phải 2xx
        data = res.json()
        if "error" in data:
            logger.error(f"Lỗi lấy thông tin Page {page_id}: {data['error']['message']}")
        return data
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Lỗi mạng khi lấy thông tin Page {page_id}: {e}")
        return {"error": str(e)}

# Cần truyền access_token và page_id vào hàm
def get_latest_posts(page_id: str, access_token: str, limit=3) -> dict:
    """Lấy các bài đăng mới nhất (Cần truyền từ main.py)."""
    url = f"https://graph.facebook.com/v19.0/{page_id}/posts"
    params = {
        "access_token": access_token, # SỬ DỤNG tham số access_token
        "limit": limit,
        "fields": "message,created_time"
    }
    try:
        res = requests.get(url, params=params, timeout=5)
        res.raise_for_status()
        data = res.json()
        if "error" in data:
            logger.error(f"Lỗi lấy bài đăng Page {page_id}: {data['error']['message']}")
        return data
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Lỗi mạng khi lấy bài đăng Page {page_id}: {e}")
        return {"error": str(e)}

# Cần truyền access_token vào hàm
def reply_comment(comment_id: str, message: str, access_token: str) -> dict:
    """Phản hồi một bình luận (Cần truyền từ main.py)."""
    url = f"https://graph.facebook.com/v19.0/{comment_id}/comments"
    params = {"access_token": access_token} # SỬ DỤNG tham số access_token
    data = {"message": message}
    try:
        response = requests.post(url, params=params, data=data, timeout=5)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Lỗi phản hồi bình luận {comment_id}: {e}")
        return {"error": str(e)}

# ====================================================================
# 2. XỬ LÝ PAYLOAD WEBHOOK VÀ GHI DB
# (Hàm này giữ nguyên cấu trúc cũ, chỉ dùng logging thay vì print)
# ====================================================================

def handle_webhook_data(data: dict, php_connect_url: str):
    """
    Trích xuất dữ liệu từ payload webhook và gửi tới connect.php.

    Args:
        data (dict): Dữ liệu JSON từ webhook POST request.
        php_connect_url (str): URL của endpoint PHP để ghi DB.
    """
    
    # Lọc dữ liệu: Chỉ xử lý sự kiện 'page'
    if data.get('object') != 'page' or not data.get('entry'):
        return

    for entry in data['entry']:
        # Lấy ID Page ngay ở đây để so sánh sau này
        idpage = entry.get('id')

        for change in entry.get('changes', []):
            # Lọc sự kiện bình luận (comment) trong trường 'feed'
            if change.get('field') == 'feed' and change.get('value', {}).get('item') == 'comment':
                value = change['value']
                
                # --- 1. Trích xuất dữ liệu ---
                idcomment = value.get('comment_id')
                idpost = value.get('post_id')
                idpersion = value.get('from', {}).get('id') # ID người comment
                message = value.get('message', '').strip()
                creatime = value.get('created_time') 
                
                # >>>>>> KIỂM TRA MỚI: BỎ QUA BÌNH LUẬN TỪ CHÍNH PAGE <<<<<<
                if idpersion == idpage:
                    logger.info(f"⏭️ Bỏ qua bình luận tự động của Page ID {idpage} để tránh vòng lặp.")
                    continue
                # >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
                
                # Bỏ qua nếu thiếu nội dung hoặc sự kiện không hợp lệ
                if not message or not idcomment or idcomment == idpost:
                    continue
                    
                # --- 2. Chuẩn bị Payload cho connect.php ---
                db_payload = {
                    "idpage": idpage,
                    "idpersion": idpersion,
                    "idpost": idpost,
                    "idcomment": idcomment,
                    "message": message,
                    "creatime": creatime,
                    "status": "PENDING",     
                    "is_replied": 0,     
                    "ai_response": None,
                    "processed_at": None
                }

                # --- 3. Gửi yêu cầu POST tới connect.php ---
                try:
                    response = requests.post(php_connect_url, json=db_payload, timeout=5)
                    
                    if response.status_code == 200 and response.json().get('status') == 'success':
                        logger.info(f"✅ Bình luận ID {idcomment} đã được ghi thành công qua PHP.")
                    else:
                        logger.error(f"❌ Lỗi ghi DB qua PHP. Code: {response.status_code}, Res: {response.text}")
                except requests.exceptions.RequestException as e:
                    logger.error(f"❌ Lỗi mạng khi gửi tới PHP: {e}")

# ====================================================================
