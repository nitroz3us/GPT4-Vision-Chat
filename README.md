# GPT4-Vision-Chat
Use GPT4-Vision API with a friendly Web Interface without having to subscribe to ChatGPT Plus. Deployed on Streamlit.

## Key Features

- **GPT4 Vision Generation:** Analyze your files and get a response from GPT4.
- **User-Friendly Interface:** Be able to use GPT4-Vision API with an interface.
- **Upload PDFs & Images:** Upload PDF documents or image files.

## Getting Started (Locally)

To get started with GPT4-Vision-Chat, follow these steps:

1. Clone the repository:

    ```bash
    git clone https://github.com/nitroz3us/GPT4-Vision-Chat.git
    ```

2. Install the required dependencies:
  
    ```bash
    pip install -r requirements.txt
    ```
    
3. Set up your ```.env``` file
    ```bash
    SUPABASE_URL = 
    SUPABASE_KEY =
    SUPABASE_BUCKET_NAME =
    ```

4. Run the application:
   
    ```bash
    streamlit run app.py --server.enableXsrfProtection=false
    ```

## Usage
1. Enter your OpenAI API Key, which can be found here [Has to be GPT4]
    - https://platform.openai.com/account/api-keys
    - https://help.openai.com/en/articles/7102672-how-can-i-access-gpt-4 [Accessing GPT4]

## Demo
<img width="1412" alt="Screenshot 2024-01-23 at 11 52 16 PM" src="https://github.com/nitroz3us/GPT4-Vision-Chat/assets/109442833/360f9c71-b2be-46c0-a6a1-2719105ae960">


## Limitations
- Maximum of 32 pages (PDF).
- Within the token limit of GPT4 Vision. 

## Why am I doing this?
- I don't see myself using ChatGPT Plus a lot, so this is a good way for me to have access to GPT4.
