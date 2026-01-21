from PIL import Image, ImageDraw
import os

def add_corners(im, rad):
    circle = Image.new('L', (rad * 2, rad * 2), 0)
    draw = ImageDraw.Draw(circle)
    draw.ellipse((0, 0, rad * 2 - 1, rad * 2 - 1), fill=255)
    
    alpha = Image.new('L', im.size, 255)
    w, h = im.size
    
    # Kích thước bo góc (15% chiều rộng ảnh)
    rad = int(w * 0.15) 
    
    # Tạo mask bo tròn
    circle = Image.new('L', (rad * 2, rad * 2), 0)
    draw = ImageDraw.Draw(circle)
    draw.ellipse((0, 0, rad * 2 - 1, rad * 2 - 1), fill=255)
    
    alpha.paste(circle.crop((0, 0, rad, rad)), (0, 0))
    alpha.paste(circle.crop((0, rad, rad, rad * 2)), (0, h - rad))
    alpha.paste(circle.crop((rad, 0, rad * 2, rad)), (w - rad, 0))
    alpha.paste(circle.crop((rad, rad, rad * 2, rad * 2)), (w - rad, h - rad))
    
    im.putalpha(alpha)
    return im

def main():
    input_path = os.path.join("Frontend", "src", "assets", "icon.png")
    output_path = os.path.join("Frontend", "src", "assets", "icon_rounded.png")
    
    if not os.path.exists(input_path):
        print(f"❌ File not found: {input_path}")
        return

    print(f"🔹 Processing: {input_path}")
    
    try:
        img = Image.open(input_path).convert("RGBA")
        
        # Bo tròn góc
        # Tính bán kính bo = 20% kích thước ảnh (khá mềm mại)
        radius = int(min(img.size) * 0.2)
        
        # Tạo mask
        mask = Image.new("L", img.size, 0)
        draw = ImageDraw.Draw(mask)
        draw.rounded_rectangle([(0, 0), img.size], radius=radius, fill=255)
        
        # Apply mask
        result = Image.new("RGBA", img.size)
        result.paste(img, (0, 0), mask=mask)
        
        result.save(output_path)
        print(f"✅ Created rounded icon: {output_path}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
