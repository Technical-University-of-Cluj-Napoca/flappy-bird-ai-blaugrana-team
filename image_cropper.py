import os
from PIL import Image

def process_4row_ghost(input_filename):
    # 1. FIND THE FILE
    # Check current folder and assets folder
    possible_paths = [input_filename, f"assets/{input_filename}", "ghost_sheet.png", "assets/ghost_sheet.png"]
    path = None
    for p in possible_paths:
        if os.path.exists(p):
            path = p
            break
            
    if path is None:
        print(f"❌ Error: Could not find '{input_filename}' or 'ghost_sheet.png'.")
        print("   Make sure the downloaded image is in the same folder as this script!")
        return

    try:
        img = Image.open(path).convert("RGBA")
        W, H = img.size
        
        # 2. GRID SETTINGS (3 Columns x 4 Rows)
        cols = 3
        rows = 4
        
        sw = W // cols
        sh = H // rows
        
        print(f"Processing '{path}'...")
        print(f"   Image Size: {W}x{H}")
        print(f"   Grid: {cols}x{rows} (Sprite size: {sw}x{sh})")
        
        # 3. SELECT THE CORRECT ROW
        # Row 0 = Back View (No eyes)
        # Row 1 = Front View (Eyes!) <--- WE WANT THIS
        # Row 2 = Side View
        # Row 3 = Side View
        target_row = 1 
        
        # Map columns to Flappy Bird animation states
        # usually: Col 0=Step, Col 1=Neutral, Col 2=Step
        frames_indices = [
            (0, target_row), # Downflap (Left step)
            (1, target_row), # Midflap  (Standing)
            (2, target_row)  # Upflap   (Right step)
        ]
        
        filenames = [
            "ghostbird-downflap.png", 
            "ghostbird-midflap.png", 
            "ghostbird-upflap.png"
        ]
        
        if not os.path.exists('assets'):
            os.makedirs('assets')

        for i, (c, r) in enumerate(frames_indices):
            # Calculate crop box
            left = c * sw
            top = r * sh
            right = left + sw
            bottom = top + sh
            
            # Crop
            sprite = img.crop((left, top, right, bottom))
            
            # 4. BACKGROUND REMOVAL
            datas = sprite.getdata()
            new_data = []
            bg_color = datas[0] # Top-left pixel is background
            
            for pixel in datas:
                # Tolerance of 30 to catch noise
                if (abs(pixel[0] - bg_color[0]) < 30 and 
                    abs(pixel[1] - bg_color[1]) < 30 and 
                    abs(pixel[2] - bg_color[2]) < 30):
                    new_data.append((0, 0, 0, 0)) # Transparent
                else:
                    new_data.append(pixel)
            
            sprite.putdata(new_data)
            
            # 5. TRIM & RESIZE
            bbox = sprite.getbbox()
            if bbox:
                sprite = sprite.crop(bbox)

            # Resize to fit inside standard bird box (34x24) or slightly larger (38x28)
            # 'thumbnail' preserves aspect ratio so it doesn't get squashed!
            sprite.thumbnail((38, 28), Image.NEAREST)
            
            # Save
            save_path = f"assets/{filenames[i]}"
            sprite.save(save_path)
            print(f"✅ Saved: {save_path} (Final Size: {sprite.size})")

        print("\n🎉 Success! The Ghost skin is ready.")
        print("Run main.py and select 'GHOST' to see it!")

    except Exception as e:
        print(f"❌ An error occurred: {e}")

# Run the function
process_4row_ghost("ghost_sheet.png")