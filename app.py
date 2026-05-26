from flask import Flask, request, send_file, jsonify
from PIL import Image, ImageDraw, ImageFont
import io
import os

app = Flask(__name__)

FONT_PATH = os.path.join(os.path.dirname(__file__), "RussoOne-Regular.ttf")
SANS_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

def wrap_text_to_width(draw, text, font_path, max_width, font_size):
    """Переносит текст на строки по ширине"""
    font = ImageFont.truetype(font_path, font_size)
    words = text.split()
    lines = []
    current = ""
    for word in words:
        test = (current + " " + word).strip()
        bbox = draw.textbbox((0, 0), test, font=font)
        if bbox[2] - bbox[0] <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines, font

def find_best_size(draw, title1, title2, font_path, max_width, max_size=110, min_size=48):
    """Подбирает максимальный размер шрифта при котором оба заголовка влезают"""
    for size in range(max_size, min_size - 1, -2):
        lines1, f1 = wrap_text_to_width(draw, title1, font_path, max_width, size)
        lines2, f2 = wrap_text_to_width(draw, title2, font_path, max_width, size)
        total_lines = len(lines1) + len(lines2)
        line_h = size + 12
        total_h = total_lines * line_h + 60  # 60 = разделитель + отступы
        if total_h < 420:  # влезает в рабочую зону
            return size, lines1, lines2
    return min_size, *[wrap_text_to_width(draw, t, font_path, max_width, min_size)[:1] for t in [title1, title2]]

def generate_cover(title1, title2, date=None, brand="БИЗНЕС-РОБОТИКС"):
    W, H = 1280, 720
    C_BLUE     = (0, 180, 255)
    C_BLUE_DIM = (0, 100, 150)
    PAD_X = 72
    MAX_W = W - PAD_X * 2

    img = Image.new("RGB", (W, H), "#0a0f1e")
    draw = ImageDraw.Draw(img)

    # Сетка
    for x in range(0, W, 48):
        draw.line([(x, 0), (x, H)], fill=(0, 50, 80), width=1)
    for y in range(0, H, 48):
        draw.line([(0, y), (W, y)], fill=(0, 50, 80), width=1)

    # Glow
    glow = Image.new("RGB", (W, H), "#0a0f1e")
    gd = ImageDraw.Draw(glow)
    for r in range(400, 0, -12):
        c = (0, max(0, 100 - r//4), min(220, 180 + r//5))
        gd.ellipse([-120-r//2, H-120-r//2, -120+r, H-120+r], fill=c)
    img = Image.blend(img, glow, 0.22)
    draw = ImageDraw.Draw(img)

    # Угловые маркеры
    lw = 2
    draw.line([(36, 28), (72, 28)], fill=C_BLUE, width=lw)
    draw.line([(36, 28), (36, 64)], fill=C_BLUE, width=lw)
    draw.line([(W-36, H-28), (W-72, H-28)], fill=C_BLUE_DIM, width=lw)
    draw.line([(W-36, H-28), (W-36, H-64)], fill=C_BLUE_DIM, width=lw)

    # Бренд — только один раз, вверху справа
    try:
        russo_brand = ImageFont.truetype(FONT_PATH, 30)
    except:
        russo_brand = ImageFont.truetype(FONT_PATH, 30)
    draw.text((W - 44, 32), brand, font=russo_brand, fill=C_BLUE, anchor="ra")

    # Подбираем оптимальный размер шрифта
    size, lines1, lines2 = find_best_size(draw, title1, title2, FONT_PATH, MAX_W)
    font_main = ImageFont.truetype(FONT_PATH, size)
    line_h = size + 14

    # Общая высота текстового блока
    has_date = bool(date and date.strip())
    russo_lg = ImageFont.truetype(FONT_PATH, 30)
    date_h = 55 if has_date else 0
    total_h = (len(lines1) + len(lines2)) * line_h + 20 + date_h  # 20 = разделитель

    # Вертикальное центрирование с небольшим смещением вниз
    y = max(100, (H - total_h) // 2 + 20)

    # title1 — белый
    for line in lines1:
        draw.text((PAD_X, y), line, font=font_main, fill=(255, 255, 255))
        y += line_h

    y += 4

    # title2 — синий
    for line in lines2:
        draw.text((PAD_X, y), line, font=font_main, fill=C_BLUE)
        y += line_h

    # Разделитель
    y += 12
    draw.rounded_rectangle([PAD_X, y, PAD_X + 70, y + 5], radius=3, fill=C_BLUE)
    y += 22

    # Дата — только если передана
    if has_date:
        draw.text((PAD_X, y), date, font=russo_lg, fill=(180, 220, 255))

    buf = io.BytesIO()
    img.save(buf, "PNG", quality=95)
    buf.seek(0)
    return buf

@app.route("/cover", methods=["POST"])
def cover():
    data = request.json or {}
    title1 = data.get("title1", "")
    title2 = data.get("title2", "")
    date   = data.get("date", "")
    brand  = data.get("brand", "БИЗНЕС-РОБОТИКС")
    buf = generate_cover(title1, title2, date, brand)
    return send_file(buf, mimetype="image/png", download_name="cover.png")

@app.route("/health")
def health():
    return jsonify({"status": "ok"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
