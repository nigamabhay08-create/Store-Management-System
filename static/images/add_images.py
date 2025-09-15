import os
import urllib.request

# List of required image filenames and placeholder URLs
images = {
    "store-front.jpg":"https://via.placeholder.com/300x300?text=store",
    "store-interior.jpg": "https://via.placeholder.com/600x400?text=Store+Interior",
    "checkout.jpg": "https://via.placeholder.com/600x400?text=Checkout",
    "laptop.jpg": "https://via.placeholder.com/300x300?text=Laptop",
    "notebook.jpg": "https://via.placeholder.com/300x300?text=Notebook",
    "coffee.jpg": "https://via.placeholder.com/300x300?text=Coffee",
    "phone.jpg": "https://via.placeholder.com/300x300?text=Phone",
    "mouse.jpg": "https://via.placeholder.com/300x300?text=Mouse",
    "bottle.jpg": "https://via.placeholder.com/300x300?text=Bottle",
    "default-product.jpg": "https://via.placeholder.com/300x300?text=Product",
}

# Path to images directory
images_dir = os.path.join("static", "images")

# Create directory if it doesn't exist
os.makedirs(images_dir, exist_ok=True)

# Download each image
for filename, url in images.items():
    filepath = os.path.join(images_dir, filename)
    if not os.path.exists(filepath):
        print(f"Downloading {filename}...")
        urllib.request.urlretrieve(url, filepath)
    else:
        print(f"{filename} already exists. Skipping.")

print("\n✅ All images are added or already present.")
