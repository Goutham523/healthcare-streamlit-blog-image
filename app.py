import warnings
import streamlit as st
from azure.storage.blob import BlobServiceClient, ContentSettings
from PIL import Image
import uuid
import io
import os

# -------------------------
# Config
# -------------------------
if "HEALTHCARE_AZURE_CONTAINER_NAME" not in st.secrets:
    st.error("Azure container name secret is missing in Streamlit Cloud.")
    st.stop()

if "HEALTHCARE_AZURE_STORAGE_CONNECTION_STRING" not in st.secrets:
    st.error("Azure storage connection string secret is missing.")
    st.stop()

CONTAINER_NAME = st.secrets["HEALTHCARE_AZURE_CONTAINER_NAME"]
CONNECTION_STRING = st.secrets["HEALTHCARE_AZURE_STORAGE_CONNECTION_STRING"]

UPLOAD_DIR = "blogs-images"


# ------------------------
# Azure Client
# ------------------------
@st.cache_resource
def get_blob_service():
    return BlobServiceClient.from_connection_string(CONNECTION_STRING)


blob_service_client = get_blob_service()
container_client = blob_service_client.get_container_client(CONTAINER_NAME)

# -------------------------
# UI
# -------------------------
Image.MAX_IMAGE_PIXELS = None
warnings.simplefilter("ignore", Image.DecompressionBombWarning)

# Max dimensions for blog images
MAX_WIDTH = 2000
MAX_HEIGHT = 2000


# -------------------------
# UI
# -------------------------
st.set_page_config(page_title="Healthcare Blog Image Uploader", layout="centered")

st.title("🖼️ Upload Image to Public Blog")
st.caption("Uploads optimized images directly to Azure Blob Storage")

uploaded_file = st.file_uploader(
    "Select an image",
    type=["png", "jpg", "jpeg", "webp", "bmp", "tiff"],
)

if uploaded_file:
    try:
        # -------------------------
        # Open Image Safely
        # -------------------------
        image = Image.open(uploaded_file)
        image = image.convert("RGB")  # Normalize format

        original_width, original_height = image.size

        # -------------------------
        # Resize if too large
        # -------------------------
        if image.width > MAX_WIDTH or image.height > MAX_HEIGHT:
            image.thumbnail((MAX_WIDTH, MAX_HEIGHT))

        optimized_width, optimized_height = image.size

        st.image(image, caption="Optimized Preview", use_container_width=True)

        if st.button("Upload to Azure"):
            with st.spinner("Optimizing and uploading..."):

                # -------------------------
                # Save Optimized Image to Memory
                # -------------------------
                buffer = io.BytesIO()
                image.save(
                    buffer,
                    format="JPEG",  # Convert to JPEG for blog
                    quality=85,  # Good balance quality/size
                    optimize=True,
                )
                buffer.seek(0)

                # -------------------------
                # Generate Unique Filename
                # -------------------------
                blob_name = f"{UPLOAD_DIR}/{uuid.uuid4()}.jpg"
                blob_client = container_client.get_blob_client(blob_name)

                # -------------------------
                # Upload to Azure
                # -------------------------
                blob_client.upload_blob(
                    buffer,
                    overwrite=True,
                    content_settings=ContentSettings(content_type="image/jpeg"),
                )

                blob_url = blob_client.url

            st.success("✅ Upload successful!")
            st.markdown("### Image Details")
            st.write(f"Original size: {original_width} x {original_height}")
            st.write(f"Optimized size: {optimized_width} x {optimized_height}")

            st.markdown("**Public URL:**")
            st.code(blob_url)

    except Exception as e:
        st.error(f"Upload failed: {str(e)}")
