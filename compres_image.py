import os
from PIL import Image
import io

UPLOAD_DIR = "/root/mafia_excel_api/uploads/avatars"
MAX_SIZE = 200
QUALITY = 85

def compress_image(file_path):
    try:
        img = Image.open(file_path)
        
        # Конвертируем в RGB
        if img.mode in ('RGBA', 'LA', 'P'):
            img = img.convert('RGB')
        
        # Ресайз
        img.thumbnail((MAX_SIZE, MAX_SIZE), Image.Resampling.LANCZOS)
        
        # Сохраняем с сжатием
        output = io.BytesIO()
        img.save(output, format='JPEG', quality=QUALITY, optimize=True)
        output.seek(0)
        
        # Перезаписываем файл
        with open(file_path, "wb") as f:
            f.write(output.read())
        
        print(f"✅ Сжат: {file_path}")
    except Exception as e:
        print(f"❌ Ошибка {file_path}: {e}")

# Сжимаем все файлы в папке
for filename in os.listdir(UPLOAD_DIR):
    file_path = os.path.join(UPLOAD_DIR, filename)
    if os.path.isfile(file_path):
        compress_image(file_path)

print("✅ ВСЕ ФАЙЛЫ ОБРАБОТАНЫ!")