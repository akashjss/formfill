import os

from PIL import Image, ImageDraw, ImageFont


def add_text_to_image(path, text, position):
    """
    Add text to an image with the first letter centered at specified coordinates
    
    Args:
        image_path (str): Path to the input image
        text (str): Text to overlay on the image
        position (tuple): Coordinates for centering the first letter
    
    Returns:
        PIL.Image: Modified image object
    """
    try:
        with Image.open(path) as img:
            # Convert image to RGBA if it isn't already
            img = img.convert('RGBA')
            
            # Create a drawing object
            draw = ImageDraw.Draw(img)
            
            # Load a default font (you can specify a different font file)
            try:
                # Try to use Arial font if available
                font = ImageFont.truetype("arial.ttf", 32)
            except OSError:
                # Fallback to default font if Arial is not available
                font = ImageFont.load_default()
            
            # Get the size of the first character
            first_char = text[0]
            first_char_bbox = draw.textbbox((0, 0), first_char, font=font)
            first_char_width = first_char_bbox[2] - first_char_bbox[0]
            first_char_height = first_char_bbox[3] - first_char_bbox[1]
            
            # Calculate the adjusted position to center the first character
            x = position[0] - first_char_width / 2
            y = position[1] - first_char_height / 2
            
            # Add text to the image at the adjusted position
            draw.text(
                (x, y),
                text,
                font=font,
                fill=(0, 0, 0, 255)  # Black color with full opacity
            )
            img.save(path, "PNG")
            
    except Exception as e:
        print(f"An error occurred: {e}")
        return None


def overlay_cursor(background_path, cursor_position, cursor_path=None):
    """
    Overlay a mouse cursor on an image at specified coordinates.
    
    Args:
        background_path (str): Path to the background PNG image
        output_path (str): Path where the output image will be saved
        cursor_position (tuple): (x, y) coordinates where to place the cursor
        cursor_path (str, optional): Path to cursor PNG image. If None, uses default cursor
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Load the background image
        background = Image.open(background_path).convert('RGBA')
        
        # Create or load cursor
        if cursor_path and os.path.exists(cursor_path):
            cursor = Image.open(cursor_path).convert('RGBA')
        else:
            # Create a simple cursor shape if no cursor image provided
            cursor = Image.new('RGBA', (20, 20), (0, 0, 0, 0))
            # Draw cursor shape
            for i in range(15):
                for j in range(15):
                    if i == 0 or j == 0:  # Create cursor outline
                        cursor.putpixel((i, j), (0, 0, 0, 255))
                    elif i == 1 or j == 1:  # Create cursor body
                        cursor.putpixel((i, j), (255, 255, 255, 255))
        
        # Ensure cursor position is within image bounds
        x, y = cursor_position
        max_x = background.width - cursor.width
        max_y = background.height - cursor.height
        x = min(max(0, x), max_x)
        y = min(max(0, y), max_y)
        
        # Create a copy of the background
        result = background.copy()
        
        # Paste the cursor onto the background using alpha compositing
        result.alpha_composite(cursor, (x, y))
        
        # Save the result
        return result
        
    except Exception as e:
        print(f"Error: {e}")
        return False
    


def scale_image_height(img, target_height=800):
    """
    Scale an image to a target height while maintaining aspect ratio.
    
    Parameters:
    input_path (str): Path to the input image
    output_path (str): Path where the scaled image will be saved
    target_height (int): Desired height in pixels (default: 800)
    
    Returns:
    tuple: New dimensions (width, height) of the scaled image
    """
    try:
        # Calculate aspect ratio
        aspect_ratio = img.width / img.height
        
        # Calculate new width based on target height and aspect ratio
        new_width = int(target_height * aspect_ratio)
        
        # Resize the image using LANCZOS resampling for best quality
        resized_img = img.resize((new_width, target_height), Image.Resampling.LANCZOS)
        return resized_img
            
    except Exception as e:
        raise Exception(f"Error processing image: {str(e)}")


def pad_image_width(image, target_width, background_color=(255, 255, 255)):
    """
    Pad a PIL image to a target width by adding equal padding on both sides.
    
    Parameters:
    image (PIL.Image): The input PIL image object
    target_width (int): Desired width in pixels
    background_color (tuple): RGB color for padding (default: white)
    
    Returns:
    PIL.Image: New padded image
    """
    if target_width <= image.width:
        return image
    
    # Calculate required padding
    total_padding = target_width - image.width
    padding_each_side = total_padding // 2
    
    # Handle odd-numbered padding
    extra_pixel = total_padding % 2
    
    # Create new image with padding
    new_image = Image.new(
        image.mode, 
        (target_width, image.height),
        background_color
    )
    
    # Paste original image in center
    paste_position = (padding_each_side + extra_pixel, 0)
    new_image.paste(image, paste_position)
    
    return new_image

def restore_from_editing(img, original_size):
    """
    Restore an image to its original dimensions after editing.
    
    Parameters:
    img (PIL.Image): The edited image
    original_size (tuple): Original (width, height) of the image
    
    Returns:
    PIL.Image: Image restored to original dimensions
    """
    try:
        # Remove padding by cropping to the non-padded area
        if img.width > img.height * (original_size[0] / original_size[1]):
            # Image was padded on sides
            target_width = int(img.height * (original_size[0] / original_size[1]))
            padding = (img.width - target_width) // 2
            img = img.crop((padding, 0, img.width - padding, img.height))
        
        # Resize back to original dimensions using LANCZOS for best quality
        restored_img = img.resize(original_size, Image.Resampling.LANCZOS)
        return restored_img
            
    except Exception as e:
        raise Exception(f"Error restoring image: {str(e)}")


def resize_for_editing(img, width, height):
    resized = scale_image_height(img, height)
    return pad_image_width(resized, width)