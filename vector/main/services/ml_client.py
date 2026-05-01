import requests

def classify_text(text):
    url_post = "http://ml-service:8000/predict"
    body_request = {"text" : text}
    default_category_id = 1
    confidence = 0
    try:
        response = requests.post(url_post, json = body_request, timeout = 2)
        response.raice_for_status()
        data = response.json()
        return data.get("category_id"), data.get("confidence")
    except requests.exceptions.RequestException:
        return default_category_id, confidence