import streamlit as st
from azure.storage.blob import BlobServiceClient, ContentSettings
from PIL import Image
import uuid
import io
import os

# -------------------------
# Config
# -------------------------
CONTAINER_NAME = st.secrets["HEALTHCARE_AZURE_CONTAINER_NAME"]
CONNECTION_STRING = st.secrets["HEALTHCARE_AZURE_STORAGE_CONNECTION_STRING"]
UPLOAD_DIR = "blogs-images"


# ------------------------
# Azure Client
# -------------------------
@st.cache_resource
def get_blob_service():
    return BlobServiceClient.from_connection_string(CONNECTION_STRING)


blob_service_client = get_blob_service()
container_client = blob_service_client.get_container_client(CONTAINER_NAME)

# -------------------------
# UI
# -------------------------
st.set_page_config(page_title="Healthcare Blog Image Uploader", layout="centered")

st.title("🖼️ Upload Image to Public Blog")
st.caption("Uploads images directly to Azure Blob Storage")

uploaded_file = st.file_uploader(
    "Select an image",
    type=["png", "jpg", "jpeg", "webp", "bmp", "tiff"],
)

if uploaded_file:
    try:
        # Preview
        image = Image.open(uploaded_file)
        st.image(image, caption="Preview", use_container_width=True)

        if st.button("Upload to Azure"):
            with st.spinner("Uploading..."):
                # Generate unique filename
                file_ext = os.path.splitext(uploaded_file.name)[1]
                blob_name = f"{UPLOAD_DIR}/{uuid.uuid4()}{file_ext}"

                blob_client = container_client.get_blob_client(blob_name)

                # Upload
                blob_client.upload_blob(
                    uploaded_file.getvalue(),
                    overwrite=True,
                    content_settings=ContentSettings(content_type=uploaded_file.type),
                )

                blob_url = blob_client.url

            st.success("✅ Upload successful!")
            st.markdown("**Public URL:**")
            st.code(blob_url)

    except Exception as e:
        st.error(f"Upload failed: {str(e)}")
