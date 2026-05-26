from flask import Flask, request, send_file, jsonify
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import io
import os
import zipfile

app = Flask(__name__)

FONT_PATH = os.path.join(os.path.dirname(__file__), "RussoOne-Regular.ttf")
try:
    SANS_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    ImageFont.truetype(SANS_PATH, 20)
except:
    SANS_PATH = FONT_PATH

THEMES = {
    "blue":   {"bg":"#0a0f1e","grid":(0,50,80),  "accent":(0,180,255), "dim":(0,100,150), "badge_bg":(0,40,70)},
    "purple": {"bg":"#12082a","grid":(50,20,80), "accent":(160,80,255),"dim":(80,30,140), "badge_bg":(50,20,90)},
    "green":  {"bg":"#071a10","grid":(10,60,30), "accent":(0,210,100), "dim":(0,100,50),  "badge_bg":(0,50,25)},
}

def draw_glow_text(img, text, pos, font, color, glow_color, glow_radius=14, max_alpha=65):
    x, y = pos
    glow_layer = Image.new("RGBA", img.size, (0,0,0,0))
    gd = ImageDraw.Draw(glow_layer)
    for offset in range(glow_radius, 0, -3):
        alpha = int(max_alpha * (1 - offset/glow_radius))
        gc = (*glow_color, alpha)
        for dx in [-offset, 0, offset]:
            for dy in [-offset, 0, offset]:
                gd.text((x+dx, y+dy), text, font=font, fill=gc)
    glow_layer = glow_layer.filter(ImageFilter.GaussianBlur(radius=glow_radius//3))
    img_rgba = img.convert("RGBA")
    img_rgba = Image.alpha_composite(img_rgba, glow_layer)
    ImageDraw.Draw(img_rgba).text((x, y), text, font=font, fill=(*color, 255))
    return img_rgba.convert("RGB")

def base_image(theme="blue"):
    T = THEMES.get(theme, THEMES["blue"])
    W, H = 1080, 1080
    CA, CD = T["accent"], T["dim"]
    img = Image.new("RGB", (W,H), T["bg"])
    draw = ImageDraw.Draw(img)
    for x in range(0,W,48): draw.line([(x,0),(x,H)], fill=T["grid"], width=1)
    for y in range(0,H,48): draw.line([(0,y),(W,y)], fill=T["grid"], width=1)
    glow_bg = Image.new("RGB",(W,H), T["bg"])
    gd = ImageDraw.Draw(glow_bg)
    for r in range(450,0,-12):
        c = (min(255,CA[0]//5), min(255,CA[1]//5), min(255,CA[2]//5))
        gd.ellipse([-150-r//2,H-150-r//2,-150+r,H-150+r], fill=c)
    img = Image.blend(img, glow_bg, 0.22)
    draw = ImageDraw.Draw(img)
    draw.line([(36,28),(72,28)], fill=CA, width=2)
    draw.line([(36,28),(36,64)], fill=CA, width=2)
    draw.line([(W-36,H-28),(W-72,H-28)], fill=CD, width=2)
    draw.line([(W-36,H-28),(W-36,H-64)], fill=CD, width=2)
    return img, CA, CD, T

def add_brand(img, CA):
    f = ImageFont.truetype(FONT_PATH, 26)
    draw = ImageDraw.Draw(img)
    bw = draw.textbbox((0,0),"БИЗНЕС-РОБОТИКС",font=f)[2]
    img = draw_glow_text(img, "БИЗНЕС-РОБОТИКС", (img.size[0]-bw-40,32), f, (255,255,255), CA, 10, 45)
    return img

def add_slide_num(img, CA, num, total):
    draw = ImageDraw.Draw(img)
    f = ImageFont.truetype(FONT_PATH, 18)
    draw.text((60,55), f"{num}/{total}", font=f, fill=CA)
    W = img.size[0]
    draw.rounded_rectangle([60,82,W-60,85], radius=2, fill=(*CA,60))
    return img

def wrap_text(draw, text, font, max_w):
    words = text.split()
    lines, cur = [], ""
    for w in words:
        test = (cur+" "+w).strip()
        if draw.textbbox((0,0),test,font=font)[2] <= max_w:
            cur = test
        else:
            if cur: lines.append(cur)
            cur = w
    if cur: lines.append(cur)
    return lines

def slide_cover(title1, title2, badge, theme="blue", date=""):
    img, CA, CD, T = base_image(theme)
    W, H = img.size
    f_brand = ImageFont.truetype(FONT_PATH, 28)
    draw = ImageDraw.Draw(img)
    bw = draw.textbbox((0,0),"БИЗНЕС-РОБОТИКС",font=f_brand)[2]
    img = draw_glow_text(img, "БИЗНЕС-РОБОТИКС", (W-bw-40,32), f_brand, (255,255,255), CA, 10, 45)
    draw = ImageDraw.Draw(img)
    f_badge = ImageFont.truetype(SANS_PATH, 22)
    bx, by = 60, 100
    bw2 = draw.textbbox((0,0),badge,font=f_badge)[2]+56
    draw.rounded_rectangle([bx,by,bx+bw2,by+46], radius=23, fill=T["badge_bg"], outline=CA, width=1)
    draw.ellipse([bx+14,by+18,bx+26,by+30], fill=CA)
    draw.text((bx+38,by+10), badge, font=f_badge, fill=CA)
    f_xl = ImageFont.truetype(FONT_PATH, 104)
    MAX_W = W-120
    l1 = wrap_text(draw, title1, f_xl, MAX_W)
    l2 = wrap_text(draw, title2, f_xl, MAX_W)
    while (len(l1)+len(l2))*(f_xl.size+18) > 560 and f_xl.size > 52:
        f_xl = ImageFont.truetype(FONT_PATH, f_xl.size-4)
        l1 = wrap_text(draw, title1, f_xl, MAX_W)
        l2 = wrap_text(draw, title2, f_xl, MAX_W)
    lh = f_xl.size+18
    y = max(210, (H-(len(l1)+len(l2))*lh+30)//2+50)
    for line in l1:
        img = draw_glow_text(img, line, (60,y), f_xl, (255,255,255), CA, 16, 60)
        y += lh
    y += 8
    for line in l2:
        img = draw_glow_text(img, line, (60,y), f_xl, CA, CA, 20, 70)
        y += lh
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle([60,y+14,150,y+20], radius=3, fill=CA)
    if date:
        f_d = ImageFont.truetype(FONT_PATH, 30)
        draw.text((60,y+32), date, font=f_d, fill=tuple(min(255,c+60) for c in CA))
    return img

def slide_tezis(accent_text, bullets, num, total, theme="blue"):
    img, CA, CD, T = base_image(theme)
    W, H = img.size
    img = add_brand(img, CA)
    img = add_slide_num(img, CA, num, total)
    draw = ImageDraw.Draw(img)
    MAX_W = W-140
    f_accent = ImageFont.truetype(FONT_PATH, 68)
    while draw.textbbox((0,0),accent_text,font=f_accent)[2] > MAX_W and f_accent.size > 38:
        f_accent = ImageFont.truetype(FONT_PATH, f_accent.size-2)
    f_bullet = ImageFont.truetype(SANS_PATH, 38)
    a_lines = wrap_text(draw, accent_text, f_accent, MAX_W)
    ACCENT_LH = f_accent.size+12
    ACCENT_H = len(a_lines)*ACCENT_LH
    GAP = 48
    BULLET_H = 110
    total_h = ACCENT_H + GAP + BULLET_H*len(bullets)
    y = max(110, (H-total_h)//2)
    for line in a_lines:
        img = draw_glow_text(img, line, (60,y), f_accent, CA, CA, 18, 72)
        y += ACCENT_LH
    draw = ImageDraw.Draw(img)
    y += GAP
    for b in bullets:
        by_ = y
        draw.ellipse([60,by_+16,78,by_+34], fill=CA)
        for line in wrap_text(draw, b, f_bullet, MAX_W-38):
            draw.text((98,by_), line, font=f_bullet, fill=(210,210,210))
            by_ += 48
        y += BULLET_H
    return img

def slide_tezis_with_plain(accent_text, bullets, plain_text, num, total, theme="blue"):
    img, CA, CD, T = base_image(theme)
    W, H = img.size
    img = add_brand(img, CA)
    img = add_slide_num(img, CA, num, total)
    draw = ImageDraw.Draw(img)
    MAX_W = W-140
    f_accent = ImageFont.truetype(FONT_PATH, 68)
    while draw.textbbox((0,0),accent_text,font=f_accent)[2] > MAX_W and f_accent.size > 38:
        f_accent = ImageFont.truetype(FONT_PATH, f_accent.size-2)
    f_bullet = ImageFont.truetype(SANS_PATH, 38)
    f_plain  = ImageFont.truetype(FONT_PATH, 46)
    a_lines = wrap_text(draw, accent_text, f_accent, MAX_W)
    plain_lines = wrap_text(draw, plain_text, f_plain, MAX_W)
    ACCENT_LH = f_accent.size+12
    ACCENT_H = len(a_lines)*ACCENT_LH
    GAP_AFTER = 48
    BULLET_H = 110
    EXTRA_GAP = 80
    PLAIN_H = len(plain_lines)*60
    total_h = ACCENT_H+GAP_AFTER+BULLET_H*len(bullets)+EXTRA_GAP+PLAIN_H
    y = max(100, (H-total_h)//2)
    for line in a_lines:
        img = draw_glow_text(img, line, (60,y), f_accent, CA, CA, 18, 72)
        y += ACCENT_LH
    draw = ImageDraw.Draw(img)
    y += GAP_AFTER
    for b in bullets:
        by_ = y
        draw.ellipse([60,by_+16,78,by_+34], fill=CA)
        for line in wrap_text(draw, b, f_bullet, MAX_W-38):
            draw.text((98,by_), line, font=f_bullet, fill=(210,210,210))
            by_ += 48
        y += BULLET_H
    y += EXTRA_GAP
    for line in plain_lines:
        draw.text((60,y), line, font=f_plain, fill=(255,255,255))
        y += 60
    return img

def slide_stat(stat_num, stat_label, context, theme="blue"):
    img, CA, CD, T = base_image(theme)
    W, H = img.size
    img = add_brand(img, CA)
    draw = ImageDraw.Draw(img)
    f_big   = ImageFont.truetype(FONT_PATH, 190)
    f_label = ImageFont.truetype(FONT_PATH, 58)
    f_ctx   = ImageFont.truetype(SANS_PATH, 36)
    MAX_W = W-120
    ctx_lines = wrap_text(draw, context, f_ctx, MAX_W)
    total_h = 210+74+40+len(ctx_lines)*52
    y = (H-total_h)//2
    bw = draw.textbbox((0,0),stat_num,font=f_big)[2]
    img = draw_glow_text(img, stat_num, ((W-bw)//2,y), f_big, CA, CA, 32, 80)
    draw = ImageDraw.Draw(img)
    y += 210
    lw = draw.textbbox((0,0),stat_label,font=f_label)[2]
    draw.text(((W-lw)//2,y), stat_label, font=f_label, fill=(255,255,255))
    y += 74
    draw.rounded_rectangle([(W-90)//2,y,(W+90)//2,y+6], radius=3, fill=CA)
    y += 40
    for line in ctx_lines:
        lw2 = draw.textbbox((0,0),line,font=f_ctx)[2]
        draw.text(((W-lw2)//2,y), line, font=f_ctx, fill=tuple(min(255,c+60) for c in CA))
        y += 52
    return img

def slide_cta(cta_text, theme="blue"):
    img, CA, CD, T = base_image(theme)
    W, H = img.size
    img = add_brand(img, CA)
    draw = ImageDraw.Draw(img)
    f_cta    = ImageFont.truetype(FONT_PATH, 70)
    f_action = ImageFont.truetype(FONT_PATH, 44)
    f_site   = ImageFont.truetype(FONT_PATH, 28)
    MAX_W, PAD_X = W-120, 60
    lines = wrap_text(draw, cta_text, f_cta, MAX_W)
    total_h = len(lines)*84+120
    y = (H-total_h)//2
    for line in lines:
        img = draw_glow_text(img, line, (PAD_X,y), f_cta, (255,255,255), CA, 14, 55)
        y += 84
    draw = ImageDraw.Draw(img)
    y += 30
    action = "Напишите нам"
    aw = draw.textbbox((0,0),action,font=f_action)[2]
    pad = 50
    draw.rounded_rectangle([PAD_X,y,PAD_X+aw+pad*2,y+86], radius=43, fill=CA)
    img = draw_glow_text(img, action, (PAD_X+pad,y+18), f_action, (10,10,30), CA, 8, 30)
    draw = ImageDraw.Draw(img)
    draw.text((PAD_X,H-72), "biz-robotics.com", font=f_site, fill=tuple(min(255,c+40) for c in CA))
    return img

def img_to_bytes(img):
    buf = io.BytesIO()
    img.save(buf, "PNG", quality=95)
    buf.seek(0)
    return buf

@app.route("/carousel", methods=["POST"])
def carousel():
    d = request.json or {}
    theme      = d.get("theme", "blue")
    title1     = d.get("title1", "")
    title2     = d.get("title2", "")
    badge      = d.get("badge", "БИЗНЕС-РОБОТИКС")
    date       = d.get("date", "")
    s2_accent  = d.get("s2_accent", "")
    s2_bullets = d.get("s2_bullets", [])
    s3_accent  = d.get("s3_accent", "")
    s3_bullets = d.get("s3_bullets", [])
    s3_plain   = d.get("s3_plain", "")
    stat_num   = d.get("stat_num", "")
    stat_label = d.get("stat_label", "")
    stat_ctx   = d.get("stat_ctx", "")
    cta_text   = d.get("cta_text", "")

    slides = [
        slide_cover(title1, title2, badge, theme, date),
        slide_tezis(s2_accent, s2_bullets, 2, 5, theme),
        slide_tezis_with_plain(s3_accent, s3_bullets, s3_plain, 3, 5, theme),
        slide_stat(stat_num, stat_label, stat_ctx, theme),
        slide_cta(cta_text, theme),
    ]

    zip_buf = io.BytesIO()
    with zipfile.ZipFile(zip_buf, 'w', zipfile.ZIP_DEFLATED) as zf:
        for i, s in enumerate(slides, 1):
            buf = io.BytesIO()
            s.save(buf, "PNG", quality=95)
            zf.writestr(f"slide_{i:02d}.png", buf.getvalue())
    zip_buf.seek(0)
    return send_file(zip_buf, mimetype="application/zip", download_name="carousel.zip")

@app.route("/cover", methods=["POST"])
def cover():
    d = request.json or {}
    img = slide_cover(
        d.get("title1",""), d.get("title2",""),
        d.get("badge","БИЗНЕС-РОБОТИКС"),
        d.get("theme","blue"), d.get("date","")
    )
    # square=true → 1080x1080 (для Telegram), иначе 1280x720
    if not d.get("square", False):
        img = img.resize((1280,720), Image.LANCZOS)
    buf = img_to_bytes(img)
    return send_file(buf, mimetype="image/png", download_name="cover.png")

@app.route("/health")
def health():
    return jsonify({"status":"ok"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
