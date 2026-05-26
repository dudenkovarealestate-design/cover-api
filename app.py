from flask import Flask, request, send_file, jsonify
from PIL import Image, ImageDraw, ImageFont
import io
import os

app = Flask(__name__)

FONT_PATH = os.path.join(os.path.dirname(__file__), "RussoOne-Regular.ttf")
SANS_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

def fit_text(draw, text, font_path, max_width, max_size=90, min_size=28):
    """Подбирает размер шрифта чтобы текст влез в max_width"""
    size = max_size
    while size >= min_size:
        font = ImageFont.truetype(font_path, size)
        bbox = draw.textbbox((0, 0), text, font=font)
        if bbox[2] - bbox[0] <= max_width:
            return font, size
        size -= 2
    return ImageFont.truetype(font_path, min_size), min_size

def wrap_text(draw, text, font_path, max_width, font_size):
    """Разбивает текст на строки если не влезает"""
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

def generate_cover(title1, title2, date=None, badge="ЕЖЕНЕДЕЛЬНЫЙ ДАЙДЖЕСТ", brand="БИЗНЕС-РОБОТИКС"):
    W, H = 1280, 720
    C_BLUE     = (0, 180, 255)
    C_BLUE_DIM = (0, 100, 150)
    MAX_W = W - 96 - 200  # отступы + место для декора

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
    for r in range(350, 0, -12):
        c = (0, max(0, 100 - r//4), min(220, 180 + r//5))
        gd.ellipse([-100-r//2, H-100-r//2, -100+r, H-100+r], fill=c)
    img = Image.blend(img, glow, 0.20)
    draw = ImageDraw.Draw(img)

    # Угловые маркеры
    lw = 2
    draw.line([(36, 28), (72, 28)],         fill=C_BLUE,     width=lw)
    draw.line([(36, 28), (36, 64)],         fill=C_BLUE,     width=lw)
    draw.line([(W-36, H-28), (W-72, H-28)], fill=C_BLUE_DIM, width=lw)
    draw.line([(W-36, H-28), (W-36, H-64)], fill=C_BLUE_DIM, width=lw)

    # Шрифты
    russo_brand = ImageFont.truetype(FONT_PATH, 34)
    russo_lg    = ImageFont.truetype(FONT_PATH, 32)
    try:
        sans = ImageFont.truetype(SANS_PATH, 20)
    except:
        sans = ImageFont.truetype(FONT_PATH, 20)

    # Бренд
    draw.text((W - 44, 32), brand, font=russo_brand, fill=C_BLUE, anchor="ra")

    # Бейдж
    bx, by = 48, 110
    bbox = draw.textbbox((0, 0), badge, font=sans)
    bw = bbox[2] - bbox[0] + 64
    bh = 46
    draw.rounded_rectangle([bx, by, bx+bw, by+bh], radius=23, fill=(0, 40, 70), outline=C_BLUE, width=1)
    draw.ellipse([bx+16, by+18, bx+28, by+30], fill=C_BLUE)
    draw.text((bx+38, by+10), badge, font=sans, fill=C_BLUE)

    # Вычисляем позиции с учётом наличия даты
    has_date = bool(date and date.strip())

    # Подбираем шрифт для title1
    font1, size1 = fit_text(draw, title1, FONT_PATH, MAX_W, max_size=90, min_size=32)

    # Для title2 — сначала пробуем в одну строку
    font2, size2 = fit_text(draw, title2, FONT_PATH, MAX_W, max_size=size1, min_size=28)

    # Если title2 не влезает в одну строку — переносим
    lines2, font2 = wrap_text(draw, title2, FONT_PATH, MAX_W, size2)

    # Высота блока
    line_h1 = size1 + 10
    line_h2 = size2 + 8
    total_text_h = line_h1 + len(lines2) * line_h2

    # Стартовая позиция — центрируем текстовый блок вертикально (смещаем вниз от центра)
    y_start = max(180, H // 2 - total_text_h // 2 + 40)

    # title1 (белый)
    draw.text((48, y_start), title1, font=font1, fill=(255, 255, 255))
    y_cur = y_start + line_h1 + 8

    # title2 (синий, возможно несколько строк)
    for line in lines2:
        draw.text((48, y_cur), line, font=font2, fill=C_BLUE)
        y_cur += line_h2

    # Разделитель
    y_cur += 8
    draw.rounded_rectangle([48, y_cur, 118, y_cur+5], radius=3, fill=C_BLUE)
    y_cur += 18

    # Дата — только если передана
    if has_date:
        draw.text((48, y_cur), date, font=russo_lg, fill=(180, 220, 255))

    buf = io.BytesIO()
    img.save(buf, "PNG", quality=95)
    buf.seek(0)
    return buf

@app.route("/cover", methods=["POST"])
def cover():
    data = request.json or {}
    title1 = data.get("title1", "")
    title2 = data.get("title2", "")
    date   = data.get("date", "")      # пустая строка = без даты
    badge  = data.get("badge", "БИЗНЕС-РОБОТИКС")
    brand  = data.get("brand", "БИЗНЕС-РОБОТИКС")

    buf = generate_cover(title1, title2, date, badge, brand)
    return send_file(buf, mimetype="image/png", download_name="cover.png")

@app.route("/health")
def health():
    return jsonify({"status": "ok"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
