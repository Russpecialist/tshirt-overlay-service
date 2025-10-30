"""
Flask API для наложения фото клиента на шаблон футболки
"""

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from PIL import Image
import requests
from io import BytesIO
import os
from datetime import datetime

app = Flask(__name__)
CORS(app)  # Разрешаем запросы из n8n

# Настройки по умолчанию (можно переопределить в запросе)
DEFAULT_SETTINGS = {
    "template_width": 1032,
    "template_height": 1176,
    "print_x": 310,
    "print_y": 280,
    "print_width": 412,
    "print_height": 550
}

def download_image(url):
    """Скачивание изображения по URL"""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return Image.open(BytesIO(response.content))
    except Exception as e:
        raise Exception(f"Ошибка загрузки изображения: {str(e)}")

def resize_to_fit(image, target_width, target_height):
    """Изменение размера с сохранением пропорций"""
    img_width, img_height = image.size
    
    # Вычисляем коэффициент масштабирования
    width_ratio = target_width / img_width
    height_ratio = target_height / img_height
    scale = min(width_ratio, height_ratio)
    
    # Новые размеры
    new_width = int(img_width * scale)
    new_height = int(img_height * scale)
    
    # Изменяем размер
    return image.resize((new_width, new_height), Image.Resampling.LANCZOS)

@app.route('/overlay', methods=['POST'])
def overlay_images():
    """
    Основной endpoint для наложения изображений
    
    POST /overlay
    Body: {
        "template_url": "URL шаблона футболки",
        "client_photo_url": "URL фото клиента",
        "settings": {
            "template_width": 1032,
            "template_height": 1176,
            "print_area": {
                "x": 310,
                "y": 280,
                "width": 412,
                "height": 550
            }
        }
    }
    """
    try:
        data = request.json
        
        # Получаем URL изображений
        template_url = data.get('template_url')
        client_photo_url = data.get('client_photo_url')
        
        if not template_url or not client_photo_url:
            return jsonify({
                'error': 'Необходимы template_url и client_photo_url'
            }), 400
        
        # Получаем настройки или используем дефолтные
        settings = data.get('settings', {})
        print_area = settings.get('print_area', {})
        
        print_x = print_area.get('x', DEFAULT_SETTINGS['print_x'])
        print_y = print_area.get('y', DEFAULT_SETTINGS['print_y'])
        print_width = print_area.get('width', DEFAULT_SETTINGS['print_width'])
        print_height = print_area.get('height', DEFAULT_SETTINGS['print_height'])
        
        print(f"[{datetime.now()}] Начало обработки")
        print(f"Template: {template_url}")
        print(f"Client photo: {client_photo_url}")
        
        # Скачиваем изображения
        template = download_image(template_url).convert('RGBA')
        client_photo = download_image(client_photo_url).convert('RGBA')
        
        print(f"Template size: {template.size}")
        print(f"Client photo size: {client_photo.size}")
        
        # Изменяем размер фото клиента под область печати
        fitted_photo = resize_to_fit(client_photo, print_width, print_height)
        
        # Центрируем в области печати
        paste_x = print_x + (print_width - fitted_photo.width) // 2
        paste_y = print_y + (print_height - fitted_photo.height) // 2
        
        print(f"Paste position: ({paste_x}, {paste_y})")
        print(f"Fitted photo size: {fitted_photo.size}")
        
        # Накладываем фото на шаблон
        template.paste(fitted_photo, (paste_x, paste_y), fitted_photo)
        
        # Сохраняем результат в память
        output = BytesIO()
        template.save(output, format='PNG', quality=95, optimize=True)
        output.seek(0)
        
        print(f"[{datetime.now()}] Обработка завершена успешно")
        
        return send_file(
            output,
            mimetype='image/png',
            as_attachment=True,
            download_name=f'mockup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png'
        )
        
    except Exception as e:
        print(f"[{datetime.now()}] Ошибка: {str(e)}")
        return jsonify({
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/health', methods=['GET'])
def health():
    """Проверка работоспособности сервиса"""
    return jsonify({
        'status': 'ok',
        'service': 'T-Shirt Overlay Service',
        'version': '1.0.0',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/', methods=['GET'])
def index():
    """Главная страница с документацией"""
    return jsonify({
        'service': 'T-Shirt Overlay Service',
        'version': '1.0.0',
        'endpoints': {
            '/health': 'GET - Проверка работоспособности',
            '/overlay': 'POST - Наложение изображения на шаблон'
        },
        'example_request': {
            'method': 'POST',
            'url': '/overlay',
            'body': {
                'template_url': 'https://example.com/template.png',
                'client_photo_url': 'https://example.com/photo.jpg',
                'settings': {
                    'print_area': {
                        'x': 310,
                        'y': 280,
                        'width': 412,
                        'height': 550
                    }
                }
            }
        }
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
