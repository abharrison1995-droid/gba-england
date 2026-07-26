from PIL import Image, ImageDraw
import os, math

out = r"C:\Users\P50\Desktop\Exiled Alvaston\Assets\Art\Placeholders"
os.makedirs(out, exist_ok=True)

def clamp(v):
    return max(0, min(255, int(v)))

def noise_tile(size, base, variance, name):
    img = Image.new("RGB", (size, size))
    px = img.load()
    br, bg, bb = [c * 255 for c in base]
    for y in range(size):
        for x in range(size):
            n = ((math.sin(x * 12.9898 + y * 78.233) * 43758.5453) % 1)
            v = (n - 0.5) * 2 * variance * 255
            r, g, b = clamp(br + v), clamp(bg + v * 0.9), clamp(bb + v * 0.7)
            if x == 0 or y == 0:
                r, g, b = int(r * 0.92), int(g * 0.92), int(b * 0.92)
            px[x, y] = (r, g, b)
    img.save(os.path.join(out, name))
    print("wrote", name)

def brick_tile(size, mortar, brick, name):
    img = Image.new("RGB", (size, size))
    px = img.load()
    brick_h, brick_w = 8, 16
    mr, mg, mb = [int(c * 255) for c in mortar]
    br, bg, bb = [int(c * 255) for c in brick]
    for y in range(size):
        for x in range(size):
            row = y // brick_h
            offset = 0 if row % 2 == 0 else brick_w // 2
            is_m = (y % brick_h == 0) or ((x + offset) % brick_w == 0)
            n = ((math.sin(x * 0.2 + y * 0.2) * 43758.5453) % 1) * 0.08 * 255
            if is_m:
                px[x, y] = (clamp(mr + n), clamp(mg + n), clamp(mb + n))
            else:
                px[x, y] = (clamp(br + n), clamp(bg + n), clamp(bb + n))
    img.save(os.path.join(out, name))
    print("wrote", name)

def char_sprite(w, h, body, skin, name):
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    br, bg, bb = [int(c * 255) for c in body]
    sr, sg, sb = [int(c * 255) for c in skin]
    d.ellipse([w // 2 - w // 3, 2, w // 2 + w // 3, 10], fill=(0, 0, 0, 90))
    d.rectangle([w // 2 - 8, 8, w // 2 - 2, 22], fill=(int(br * 0.85), int(bg * 0.85), int(bb * 0.85), 255))
    d.rectangle([w // 2 + 2, 8, w // 2 + 8, 22], fill=(int(br * 0.85), int(bg * 0.85), int(bb * 0.85), 255))
    d.rectangle([w // 2 - 10, 20, w // 2 + 10, 42], fill=(br, bg, bb, 255))
    d.ellipse([w // 2 - 8, 39, w // 2 + 8, 57], fill=(sr, sg, sb, 255))
    d.point((w // 2 - 3, 49), fill=(0, 0, 0, 255))
    d.point((w // 2 + 2, 49), fill=(0, 0, 0, 255))
    img.save(os.path.join(out, name))
    print("wrote", name)

def bush(w, h, name):
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.ellipse([2, 2, w - 2, h - 2], fill=(71, 107, 51, 255))
    d.ellipse([w // 2 - 18, h // 2 - 6, w // 2 + 2, h // 2 + 14], fill=(78, 118, 56, 255))
    d.ellipse([w // 2 - 2, h // 2 - 8, w // 2 + 18, h // 2 + 12], fill=(64, 96, 46, 255))
    img.save(os.path.join(out, name))
    print("wrote", name)

def tree(w, h, name):
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rectangle([w // 2 - 3, 4, w // 2 + 3, 26], fill=(89, 56, 31, 255))
    d.ellipse([w // 2 - 18, 26, w // 2 + 18, 58], fill=(56, 97, 46, 255))
    d.ellipse([w // 2 - 20, 30, w // 2 - 2, 52], fill=(64, 112, 53, 255))
    d.ellipse([w // 2 + 2, 32, w // 2 + 20, 54], fill=(50, 87, 41, 255))
    img.save(os.path.join(out, name))
    print("wrote", name)

def loot(w, h, name):
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.ellipse([w // 2 - 10, h // 2 - 11, w // 2 + 10, h // 2 + 7], fill=(115, 77, 38, 255))
    d.rectangle([w // 2 - 8, h // 2 + 4, w // 2 + 8, h // 2 + 8], fill=(92, 61, 31, 255))
    img.save(os.path.join(out, name))
    print("wrote", name)

noise_tile(64, (0.35, 0.45, 0.28), 0.08, "tex_grass.png")
noise_tile(64, (0.55, 0.52, 0.45), 0.06, "tex_stone.png")
noise_tile(64, (0.62, 0.58, 0.48), 0.05, "tex_path.png")
brick_tile(64, (0.42, 0.40, 0.38), (0.32, 0.30, 0.28), "tex_dungeon_floor.png")
brick_tile(64, (0.62, 0.55, 0.42), (0.45, 0.38, 0.28), "tex_dungeon_wall.png")
char_sprite(48, 64, (0.35, 0.45, 0.7), (0.85, 0.7, 0.55), "spr_hero.png")
char_sprite(48, 64, (0.45, 0.22, 0.18), (0.75, 0.6, 0.45), "spr_bandit.png")
bush(48, 40, "spr_bush.png")
tree(48, 72, "spr_tree.png")
loot(32, 32, "spr_loot.png")
print("DONE", sorted(os.listdir(out)))
