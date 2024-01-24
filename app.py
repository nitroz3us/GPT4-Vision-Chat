import streamlit as st
import fitz
import os
import string
from PIL import Image
from io import BytesIO
from openai import OpenAI
from urllib.parse import urlparse, unquote
from supabase import create_client, Client
from dotenv import load_dotenv


st.set_page_config(layout="centered")
st.title("GPT-4 Vision API")
load_dotenv()
supabase_url = os.environ.get("SUPABASE_URL") or st.secret("SUPABASE_URL")
supabase_key = os.environ.get("SUPABASE_KEY") or st.secret("SUPABASE_KEY")
supabase_bucket_name = os.environ.get("SUPABASE_BUCKET_NAME") or st.secret("SUPABASE_BUCKET_NAME")
supabase: Client = create_client(supabase_url, supabase_key)


# Convert PDF to image, enumerate pages
def convert_pdf_to_images(data: bytes, pdf_filename: str):
    pdf_document = fitz.open("pdf", data)

    # Use string.ascii_lowercase for lowercase letters
    alphabet = string.ascii_lowercase

    # Check if the total number of pages exceeds 32
    if pdf_document.page_count > 32:
        print("Too many slides. Limit exceeded (32 slides max).")
        return {"error": "Too many slides. Limit exceeded (32 slides max.)", "urls": []}

    for page_number in range(pdf_document.page_count):
        print("PDF converting to images... \n")
        page = pdf_document.load_page(page_number)
        resolution_parameter = 100

        image = page.get_pixmap(dpi = resolution_parameter)

        pil_image = Image.frombytes("RGB", (image.width, image.height), image.samples)
        image_bytes_io = BytesIO()
        pil_image.save(image_bytes_io, format="PNG")
        image_bytes = image_bytes_io.getvalue()

        numeric_part = page_number // len(alphabet) + 1
        letter = alphabet[page_number % len(alphabet)]
        combined_name = f"{numeric_part}{letter}"
        # Upload image to supabase storage
        upload_image_to_supabase(image_bytes, pdf_filename, combined_name)

    pdf_document.close()

    # Return success message if there's no error
    return {"success": "File processed successfully.", "urls": []}

# Upload those pages to supabase storage, create a folder using the name of the PDF file, and store the images in that folder
def upload_image_to_supabase(image_bytes: bytes, pdf_filename: str, page_name: str):
    print("Uploading images... \n")
    path_on_supastorage = f"{pdf_filename}/page_{page_name}.png"
    supabase.storage.from_(supabase_bucket_name).upload(file=image_bytes, path=path_on_supastorage, file_options={"content-type": "image/png"})

# Get signed url for file in supabase storage, change to get the folder name and get all files in that folder
def retrieve_urls(pdf_filename):
    """
    Retrieve signed url for image files in supabase storage
    """
    # get all files in bucket
    folder_path = f"{pdf_filename}/"
    list_files_folder = supabase.storage.from_(supabase_bucket_name).list(path=folder_path)
    print(list_files_folder) # works

    # get signed urls for all files
    image_urls = []
    for file_object in list_files_folder:
        file_name = file_object['name']
        file_path = f"{pdf_filename}/{file_name}"
        get_all_signed_url = supabase.storage.from_(supabase_bucket_name).create_signed_url(file_path, 60) # 60 seconds
        image_urls.append(get_all_signed_url['signedURL'])
    print("\nRetrieving SignedURL: \n",image_urls) # works
    return image_urls

# delete files from supabase
def delete_files(pdf_filename):
    list_of_url = retrieve_urls(pdf_filename)
    list_of_file_paths = []
    for image_url in list_of_url:
        url_object = urlparse(image_url)
        parts = url_object.path.split("/")
        pdf_filename = parts[-2] if len(parts) >= 2 else ""
        page_filename = unquote(parts[-1]) if parts else ""
        file_path = f"{pdf_filename}/{page_filename}"

        list_of_file_paths.append(file_path)

    print("List of File Paths: ", list_of_file_paths)

    for file_path in list_of_file_paths:
        try:
            supabase.storage.from_(supabase_bucket_name).remove(file_path)
            print(f"File '{file_path}' deleted successfully.")
        except Exception as e:
            print(f"Error deleting file '{file_path}': {e}")

def main():
    api_key = st.text_input(
        "Enter your API Key here",
        key="placeholder",
        type="password",
        max_chars=51,
        help="You can find your API key at https://help.openai.com/en/articles/7102672-how-can-i-access-gpt-4",
    )
    client = OpenAI(api_key=api_key)
    
    uploaded_file = st.file_uploader("Upload an image", type=["jpg", "png", "jpeg", "pdf"])
    toggle_prompt = st.toggle("Toggle Prompt", value=True, help="Toggle to add your own prompt")


    if toggle_prompt:
        user_prompt = st.text_area(
            "Add your prompt here:",
            disabled=not toggle_prompt,
            
        )

    submit_btn = st.button("Submit", type="secondary")
    if uploaded_file is not None and submit_btn and api_key:
        st.info("Processing file...")

        # Caveat: No matter the file type, it will be processed the same way as how PDFs are processed.
        # Saves effort and time, didn't want to create a separate function just for images only so just process everything like as if it's a PDF.
        conversion_result = convert_pdf_to_images(uploaded_file.read(), uploaded_file.name)

        if "error" in conversion_result:
            st.error(conversion_result["error"])
            # Delete files from supabase storage
            delete_files(uploaded_file.name)
        else:
            st.success(conversion_result["success"])
            
            print("File type: ",uploaded_file.type)

            if uploaded_file.type == "image/png" or uploaded_file.type == "image/jpg" or uploaded_file.type == "image/jpeg":
                st.image(uploaded_file, caption="Uploaded Image", use_column_width=True)

            image_urls = retrieve_urls(uploaded_file.name)

            with st.spinner("Analysing the image ..."):
                prompt_text = user_prompt
                
                messages = [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt_text},
                        ],
                    }
                ]

                # Append image URLs to the "content" of the user message
                for image_url in image_urls:
                    messages.append(
                        {
                            "role": "user",
                            "content": [
                                {"type": "image_url", "image_url": {"url": image_url}},
                            ],
                        }
                    )

                # Make the request to the OpenAI API
                try:
                    # Stream the response
                    full_response = ""
                    message_placeholder = st.empty()
                    for completion in client.chat.completions.create(
                        model="gpt-4-vision-preview", messages=messages, 
                        max_tokens=1200, stream=True
                    ):
                        # Check if there is content to display
                        if completion.choices[0].delta.content is not None:
                            full_response += completion.choices[0].delta.content
                            message_placeholder.markdown(full_response + "▌")
                    # Final update to placeholder after the stream ends
                    message_placeholder.markdown(full_response)
                    # Finally delete files from supabase storage
                    delete_files(uploaded_file.name)
                except Exception as e:
                    delete_files(uploaded_file.name)
                    st.error(f"An error occurred: {e}")      
    else:
    # Warnings for user action required
        if not uploaded_file and submit_btn:
            st.warning("Please upload a file.", icon="⚠️")
        if not api_key:
            st.warning("Please enter your OpenAI API key.", icon="⚠️" )

   
if __name__ == "__main__":
    main()
