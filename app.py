from flask import Flask, request, send_file, jsonify
from PIL import Image, ImageDraw, ImageFont
import io
import os

app = Flask(__name__)

FONT_PATH = os.path.join(os.path.dirname(__file__), "RussoOne-Regular.ttf")
SANS_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

def generate_cover(title1, title2, date, badge="ЕЖЕНЕДЕЛЬНЫЙ ДАЙДЖЕСТ", brand="БИЗНЕС-РОБОТИКС"):
    W, H = 1280, 720
    C_BLUE     = (0, 180, 255)
    C_BLUE_DIM = (0, 100, 150)

    img = Image.new("RGB", (W, H), "#0a0f1e")
    draw = ImageDraw.Draw(img)

    for x in range(0, W, 48):
        draw.line([(x, 0), (x, H)], fill=(0, 50, 80), width=1)
    for y in range(0, H, 48):
        draw.line([(0, y), (W, y)], fill=(0, 50, 80), width=1)

    glow = Image.new("RGB", (W, H), "#0a0f1e")
    gd = ImageDraw.Draw(glow)
    for r in range(350, 0, -12):
        c = (0, max(0, 100 - r//4), min(220, 180 + r//5))
        gd.ellipse([-100-r//2, H-100-r//2, -100+r, H-100+r], fill=c)
    img = Image.blend(img, glow, 0.20)
    draw = ImageDraw.Draw(img)

    lw = 2
    draw.line([(36, 28), (72, 28)],         fill=C_BLUE,     width=lw)
    draw.line([(36, 28), (36, 64)],         fill=C_BLUE,     width=lw)
    draw.line([(W-36, H-28), (W-72, H-28)], fill=C_BLUE_DIM, width=lw)
    draw.line([(W-36, H-28), (W-36, H-64)], fill=C_BLUE_DIM, width=lw)

    russo_xl    = ImageFont.truetype(FONT_PATH, 90)
    russo_lg    = ImageFont.truetype(FONT_PATH, 36)
    russo_brand = ImageFont.truetype(FONT_PATH, 34)
    try:
        sans = ImageFont.truetype(SANS_PATH, 20)
    except:
        sans = ImageFont.truetype(FONT_PATH, 20)

    draw.text((W - 44, 32), brand, font=russo_brand, fill=C_BLUE, anchor="ra")

    bx, by = 48, 130
    bbox = draw.textbbox((0, 0), badge, font=sans)
    bw = bbox[2] - bbox[0] + 64
    bh = 46
    draw.rounded_rectangle([bx, by, bx+bw, by+bh], radius=23, fill=(0, 40, 70), outline=C_BLUE, width=1)
    draw.ellipse([bx+16, by+18, bx+28, by+30], fill=C_BLUE)
    draw.text((bx+38, by+10), badge, font=sans, fill=C_BLUE)

    y_title = 220
    draw.text((48, y_title),       title1, font=russo_xl, fill=(255, 255, 255))
    draw.text((48, y_title + 100), title2, font=russo_xl, fill=C_BLUE)

    dy = y_title + 208
    draw.rounded_rectangle([48, dy, 118, dy+5], radius=3, fill=C_BLUE)
    draw.text((48, dy + 22), date, font=russo_lg, fill=(180, 220, 255))

    buf = io.BytesIO()
    img.save(buf, "PNG", quality=95)
    buf.seek(0)
    return buf

@app.route("/cover", methods=["POST"])
def cover():
    data = request.json or {}
    title1 = data.get("title1", "AI-роботы:")
    title2 = data.get("title2", "дайджест недели")
    date   = data.get("date",   "")
    badge  = data.get("badge",  "ЕЖЕНЕДЕЛЬНЫЙ ДАЙДЖЕСТ")
    brand  = data.get("brand",  "БИЗНЕС-РОБОТИКС")

    buf = generate_cover(title1, title2, date, badge, brand)
    return send_file(buf, mimetype="image/png", download_name="cover.png")

@app.route("/health")
def health():
    return jsonify({"status": "ok"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
