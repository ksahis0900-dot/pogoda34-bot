from PIL import Image
import os
import glob

def compress():
    print("Compressing images...")
    files = glob.glob("images/*.png")
    for f in files:
        output = f.replace(".png", ".jpg")
        try:
            with Image.open(f) as img:
                img = img.convert("RGB")
                img.save(output, "JPEG", quality=80, optimize=True)
            print(f"Compressed {f} -> {output}")
            os.remove(f) # Удаляем оригинал, чтобы не занимал место
        except Exception as e:
            print(f"Error processing {f}: {e}")

if __name__ == "__main__":
    compress()
