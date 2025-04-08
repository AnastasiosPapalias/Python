Below is the revised how-to guide in Markdown (`.md`) format, with all references to Git and `git clone` removed. The guide still includes detailed instructions for creating a Python app to download TikTok videos, with error handling, support for multiple downloads, a command-line interface, and optional enhancements. The script remains functional and includes a `requirements.txt` file for easy dependency installation.

---

# How to Build a Python App to Download TikTok Videos

This guide will walk you through creating a Python application to download TikTok videos using the `pyktok` library. The app includes error handling, support for downloading multiple videos, and a simple command-line interface. By the end, you'll have a working script that can download TikTok videos and save their metadata to a CSV file.

## Table of Contents
- [Prerequisites](#prerequisites)
- [Step 1: Set Up Your Environment](#step-1-set-up-your-environment)
- [Step 2: Install Dependencies](#step-2-install-dependencies)
- [Step 3: Install ChromeDriver for Selenium](#step-3-install-chromedriver-for-selenium)
- [Step 4: Create the Python Script](#step-4-create-the-python-script)
- [Step 5: Run the Script](#step-5-run-the-script)
- [Step 6: Verify the Output](#step-6-verify-the-output)
- [Step 7: Troubleshooting](#step-7-troubleshooting)
- [Step 8: Legal and Ethical Considerations](#step-8-legal-and-ethical-considerations)
- [Step 9: Optional Enhancements](#step-9-optional-enhancements)
- [License](#license)

## Prerequisites
Before you begin, ensure you have the following:
- **Python 3.9 or later**: Download and install Python from [python.org](https://www.python.org/downloads/).
- **Google Chrome Browser**: Installed on your system, as the script uses Chrome for automation.
- **A Code Editor**: Such as Visual Studio Code (VS Code) for editing the script.

## Step 1: Set Up Your Environment
1. **Create a Project Directory**:
   - Create a new folder for your project (e.g., `tiktok-downloader`) and navigate to it in your terminal or command prompt:
     ```bash
     mkdir tiktok-downloader
     cd tiktok-downloader
     ```

2. **Create a Virtual Environment** (recommended):
   - This keeps dependencies isolated.
   ```bash
   python -m venv env
   ```
   - Activate the virtual environment:
     - On Windows:
       ```bash
       env\Scripts\activate
       ```
     - On macOS/Linux:
       ```bash
       source env/bin/activate
       ```

3. **Verify Python Version**:
   - Ensure you're using Python 3.9 or later:
     ```bash
     python --version
     ```

## Step 2: Install Dependencies
The script requires several Python libraries. A `requirements.txt` file is provided for easy installation.

1. **Create a `requirements.txt` File**:
   - In your project directory, create a file named `requirements.txt` with the following content:
     ```
     pyktok==0.0.19
     beautifulsoup4==4.12.2
     browser-cookie3==0.19.1
     numpy==1.26.0
     pandas==2.1.1
     selenium==4.14.0
     ```

2. **Install the Dependencies**:
   - Run the following command to install all required libraries:
     ```bash
     pip install -r requirements.txt
     ```

   - These specific versions ensure compatibility. You can update them if newer versions are available and compatible.

## Step 3: Install ChromeDriver for Selenium
The `pyktok` library uses `selenium` to automate browser interactions, which requires ChromeDriver.

1. **Check Your Chrome Version**:
   - Open Chrome and go to `chrome://version` to see your browser version (e.g., 118.0.5993.70).

2. **Download ChromeDriver**:
   - Visit the [ChromeDriver website](https://sites.google.com/chromium.org/driver/) and download the version that matches your Chrome browser.
   - For example, if your Chrome version is 118.x, download ChromeDriver 118.x.

3. **Set Up ChromeDriver**:
   - Extract the downloaded `chromedriver` executable.
   - Add it to your system’s PATH:
     - On Windows: Move `chromedriver.exe` to a directory like `C:\Program Files\ChromeDriver` and add that directory to your PATH.
     - On macOS/Linux: Move `chromedriver` to `/usr/local/bin/`:
       ```bash
       sudo mv chromedriver /usr/local/bin/
       sudo chmod +x /usr/local/bin/chromedriver
       ```
   - Alternatively, you can specify the path to ChromeDriver in the script (see Step 4).

4. **Verify ChromeDriver**:
   - Run the following command to ensure it’s working:
     ```bash
     chromedriver --version
     ```

## Step 4: Create the Python Script
The script provides a command-line interface to download TikTok videos. It supports downloading a single video or multiple videos from a list of URLs, with error handling and metadata logging.

1. **Create a File Named `tiktok_downloader.py`**:
   - In your project directory, create a file named `tiktok_downloader.py` and copy the following code into it:

   ```python
   import pyktok as pyk
   import pandas as pd
   import sys
   import argparse
   from selenium.common.exceptions import WebDriverException
   from urllib.error import URLError

   def setup_browser():
       """Set up the browser for pyktok."""
       try:
           # Specify the browser (Chrome)
           # If ChromeDriver is not in PATH, specify its path:
           # pyk.specify_browser('chrome', driver_path='path/to/chromedriver')
           pyk.specify_browser('chrome')
           print("Browser setup completed.")
       except WebDriverException as e:
           print(f"Error setting up browser: {e}")
           print("Ensure ChromeDriver is installed and in your PATH.")
           sys.exit(1)

   def download_tiktok_video(url, save_video=True, metadata_file='metadata.csv'):
       """Download a TikTok video and save its metadata."""
       try:
           print(f"Downloading video from: {url}")
           pyk.save_tiktok(url, save_video, metadata_file)
           print(f"Successfully downloaded video from {url}")
       except URLError as e:
           print(f"Network error while downloading {url}: {e}")
       except Exception as e:
           print(f"Error downloading {url}: {e}")

   def main():
       """Main function to handle command-line arguments and download videos."""
       # Set up argument parser
       parser = argparse.ArgumentParser(description="Download TikTok videos using pyktok.")
       parser.add_argument('--url', type=str, help="Single TikTok video URL to download")
       parser.add_argument('--file', type=str, help="Path to a text file containing TikTok URLs (one per line)")
       parser.add_argument('--no-video', action='store_false', help="Only save metadata, don't download the video")
       parser.add_argument('--output', type=str, default='metadata.csv', help="Output CSV file for metadata (default: metadata.csv)")

       args = parser.parse_args()

       # Set up the browser
       setup_browser()

       # Download a single video if URL is provided
       if args.url:
           download_tiktok_video(args.url, save_video=args.no_video, metadata_file=args.output)

       # Download multiple videos if a file is provided
       elif args.file:
           try:
               with open(args.file, 'r') as f:
                   urls = [line.strip() for line in f if line.strip()]
               if not urls:
                   print("No URLs found in the file.")
                   sys.exit(1)

               print(f"Found {len(urls)} URLs to download.")
               for url in urls:
                   download_tiktok_video(url, save_video=args.no_video, metadata_file=args.output)

           except FileNotFoundError:
               print(f"Error: File {args.file} not found.")
               sys.exit(1)
           except Exception as e:
               print(f"Error reading file {args.file}: {e}")
               sys.exit(1)

       else:
           print("Please provide a URL (--url) or a file with URLs (--file).")
           parser.print_help()
           sys.exit(1)

   if __name__ == "__main__":
       main()
   ```

2. **Explanation of the Script**:
   - **Command-Line Interface**: The script uses `argparse` to accept arguments for a single URL (`--url`), a file with multiple URLs (`--file`), an option to skip video downloads (`--no-video`), and a custom metadata file name (`--output`).
   - **Error Handling**: The script handles network errors, file errors, and browser setup issues gracefully.
   - **Modularity**: Functions like `setup_browser` and `download_tiktok_video` make the code reusable and easier to maintain.
   - **Metadata**: Video metadata is saved to a CSV file (default: `metadata.csv`).

3. **Create a File with URLs (Optional)**:
   - If you want to download multiple videos, create a file named `urls.txt` in your project directory with one TikTok URL per line. For example:
     ```
     https://www.tiktok.com/@card_guardstore/video/7351492424620870945
     https://www.tiktok.com/@another_user/video/123456789
     ```

## Step 5: Run the Script
1. **Download a Single Video**:
   - Run the script with a single URL:
     ```bash
     python tiktok_downloader.py --url "https://www.tiktok.com/@card_guardstore/video/7351492424620870945"
     ```
   - This will download the video and save its metadata to `metadata.csv`.

2. **Download Multiple Videos**:
   - Run the script with a file containing URLs:
     ```bash
     python tiktok_downloader.py --file urls.txt
     ```
   - This will download all videos listed in `urls.txt`.

3. **Only Save Metadata (No Video)**:
   - Use the `--no-video` flag to only save metadata:
     ```bash
     python tiktok_downloader.py --url "https://www.tiktok.com/@card_guardstore/video/7351492424620870945" --no-video
     ```

4. **Custom Metadata File**:
   - Specify a different metadata file name:
     ```bash
     python tiktok_downloader.py --url "https://www.tiktok.com/@card_guardstore/video/7351492424620870945" --output "tiktok_data.csv"
     ```

## Step 6: Verify the Output
- **Downloaded Videos**: Check your project directory for the video files (e.g., `7351492424620870945.mp4`).
- **Metadata**: Open the `metadata.csv` file (or your custom file) to view the video metadata, such as the video ID, URL, and description.

## Step 7: Troubleshooting
- **Error: "ChromeDriver not found"**:
  - Ensure ChromeDriver is installed and in your PATH (see Step 3).
  - Alternatively, specify the path in the script:
    ```python
    pyk.specify_browser('chrome', driver_path='path/to/chromedriver')
    ```
- **Error: "Module not found"**:
  - Verify that all dependencies are installed (`pip install -r requirements.txt`).
- **Video Not Downloading**:
  - Ensure the TikTok URL is correct and publicly accessible.
  - Check if you need to log in to TikTok. You may need to handle cookies or authentication manually (not covered in this script).
- **Network Errors**:
  - Ensure you have a stable internet connection.
  - Retry the download if the error persists.

## Step 8: Legal and Ethical Considerations
- **TikTok’s Terms of Service**: Downloading videos may violate TikTok’s terms of service. Use this tool responsibly and only for personal use or with explicit permission from the content creator.
- **Copyright**: Respect the intellectual property rights of TikTok creators. Do not redistribute or use downloaded videos without permission.
- **Privacy**: Avoid downloading or sharing videos that contain personal or sensitive information.

## Step 9: Optional Enhancements
1. **Add a GUI with Streamlit**:
   - Install Streamlit:
     ```bash
     pip install streamlit
     ```
   - Create a new file `app.py` in your project directory with the following code:
     ```python
     import streamlit as st
     import pyktok as pyk
     import pandas as pd

     st.title("TikTok Video Downloader")

     # Set up the browser
     pyk.specify_browser('chrome')

     # Input field for TikTok URL
     url = st.text_input("Enter TikTok Video URL:")

     # Download button
     if st.button("Download"):
         if url:
             st.write("Downloading...")
             try:
                 pyk.save_tiktok(url, True, 'metadata.csv')
                 st.success("Video downloaded successfully!")
             except Exception as e:
                 st.error(f"Error: {e}")
         else:
             st.error("Please enter a valid URL.")

     # Display the CSV file
     if st.button("Show Metadata"):
         try:
             df = pd.read_csv('metadata.csv')
             st.write(df)
         except FileNotFoundError:
             st.error("Metadata file not found.")
     ```
   - Run the Streamlit app:
     ```bash
     streamlit run app.py
     ```

2. **Add Logging**:
   - Add logging to track downloads and errors by modifying `tiktok_downloader.py`:
     ```python
     import logging

     logging.basicConfig(filename='tiktok_downloader.log', level=logging.INFO,
                         format='%(asctime)s - %(levelname)s - %(message)s')

     # In download_tiktok_video function:
     logging.info(f"Successfully downloaded video from {url}")
     logging.error(f"Error downloading {url}: {e}")
     ```

3. **Handle Authentication**:
   - If TikTok requires login, you may need to use `browser-cookie3` to extract cookies from your browser and pass them to `pyktok`. This is an advanced feature and requires additional setup.

## License
This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

### Final Notes
- Test the script in your environment to ensure compatibility with your system and Chrome version.
- If you encounter issues, feel free to reach out for assistance.
- Contributions are welcome! If you have improvements or bug fixes, consider sharing them.

### Files to Upload to GitHub
1. **README.md**: The content above.
2. **tiktok_downloader.py**: The main script.
3. **requirements.txt**: The dependencies file.
4. **urls.txt** (optional): A sample file with TikTok URLs.
5. **app.py** (optional): The Streamlit GUI script.
6. **LICENSE**: An MIT License file (or your preferred license).

Happy downloading! 🎥

---

You can now upload these files directly to GitHub as part of your repository. Let me know if you need further adjustments!
