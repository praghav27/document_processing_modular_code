import os
from PIL import Image
from io import BytesIO
from config import IMAGES_DIR


class ImageStorage:
    """Handle image/figure-related storage operations"""
    
    def __init__(self):
        pass
    
    def save_figure_image_bytes(self, image_bytes: bytes, filename: str, figure_index: int) -> str:
        """Save figure image from raw bytes data"""
        try:
            img_filename = f"{filename}_figure_{figure_index}.png"
            img_path = os.path.join(IMAGES_DIR, img_filename)
            
            # Try to open with PIL to validate and convert to PNG
            try:
                img = Image.open(BytesIO(image_bytes))
                img.save(img_path, "PNG")
                print(f"💾 Saved figure image: {img_path}")
            except Exception:
                # If PIL fails, save raw bytes
                with open(img_path, 'wb') as f:
                    f.write(image_bytes)
                print(f"💾 Saved raw image bytes: {img_path}")
            
            return img_path
        except Exception as e:
            print(f"❌ Error saving figure image {figure_index}: {e}")
            return None
    
    def save_figure_text(self, text_content: str, filename: str, figure_index: int) -> str:
        """Save figure text content"""
        txt_filename = f"{filename}_figure_{figure_index}.txt"
        txt_path = os.path.join(IMAGES_DIR, txt_filename)
        
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write(text_content)
        
        print(f"💾 Saved figure text: {txt_path}")
        return txt_path