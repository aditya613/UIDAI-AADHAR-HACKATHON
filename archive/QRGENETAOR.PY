import qrcode
import os
from datetime import datetime

def generate_qr_from_link(web_link, output_filename=None, output_dir="qr_codes"):
    """
    Generate QR code from a web link
    
    Args:
        web_link (str): The web URL to encode
        output_filename (str): Name of output file (without extension)
        output_dir (str): Directory to save QR codes
    
    Returns:
        str: Path to saved QR code image
    """
    # Create output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Generate filename if not provided
    if output_filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"qr_code_{timestamp}"
    
    # Create QR code instance
    qr = qrcode.QRCode(
        version=1,  # Controls size (1-40)
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,  # Size of each box in pixels
        border=4,  # Border in boxes
    )
    
    # Add web link data
    qr.add_data(web_link)
    qr.make(fit=True)
    
    # Create image
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Save image
    file_path = os.path.join(output_dir, f"{output_filename}.png")
    img.save(file_path)
    
    print(f"✓ QR Code generated: {file_path}")
    return file_path


def generate_multiple_qrs(links_list, output_dir="qr_codes"):
    """
    Generate QR codes for multiple links
    
    Args:
        links_list (list): List of web links
        output_dir (str): Directory to save QR codes
    
    Returns:
        list: Paths to all generated QR codes
    """
    generated_files = []
    for i, link in enumerate(links_list, 1):
        filename = f"qr_code_{i}"
        path = generate_qr_from_link(link, filename, output_dir)
        generated_files.append(path)
    
    return generated_files


# Example usage
if __name__ == "__main__":
    # Single QR code
    print("Generating QR Code from Web Link...\n")
    
    
    # Example 3: Custom link
    print("\n" + "="*50)
    print("Custom Link QR Generator")
    print("="*50)
    custom_link = input("Enter web link to convert to QR: ")
    if custom_link:
        generate_qr_from_link(custom_link, "custom_qr")
