import requests
import base64
import io
from PIL import Image
from constants import API_URL, API_KEY
def compress(image_path, max_dimension=500):
    with open(image_path, "rb") as image_file:
        image_data = image_file.read()
    image = Image.open(io.BytesIO(image_data))
    width, height = image.size
    
    if max(width, height) > max_dimension:
        scaling_factor = max_dimension / max(width, height)
        new_width = int(width * scaling_factor)
        new_height = int(height * scaling_factor)
        image = image.resize((new_width, new_height), Image.LANCZOS)
    
    buffered = io.BytesIO()
    image.save(buffered, format="JPEG")
    img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
    
    return f"data:image/jpeg;base64,{img_str}"

def prompt(prompt, image_path, api_url, api_key):
    base64_image = compress(image_path)

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    payload = {
        "model": "gpt-4o",
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": base64_image
                        }
                    }
                ]
            }
        ],
        "max_tokens": 3000
    }

    response = requests.post(api_url, headers=headers, json=payload)
    
    if response.status_code == 200:
        return response.json()['choices'][0]['message']['content']
    else:
        return f"Error: {response.status_code}, {response.text}"

api_url = API_URL
api_key = API_KEY
prompt = "Đọc thực đơn trong hình, xuất dữ liệu ra dạng JSON. Chỉ đưa ra raw JSON ngắn gọn không cần định dạng, không lời dẫn. Nếu như giá của sản phẩm được viết dưới dạng 15K (xK), hiểu K là 1000. Hãy nhân giá sản phẩm với 1000. Nếu như giá của sản phẩm viết dưới dạng 15.000 (hay xx.xxx), hãy đổi về integer, ví dụ 15000"
image_path = "/Users/ndc/desktop/JagerDiscord/restructure/utils/image.png"


#bot ngu vkl @@
result = prompt(prompt, image_path, api_url, api_key)
print(result)