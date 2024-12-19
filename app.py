from flask import Flask, request, jsonify
import threading
import os
import yt_dlp

# Initialize Flask application
app = Flask(__name__)

# Global variable to track download progress
progress = 0

def download_video(url):
    global progress
    progress = 0

    # Progress hook function to track download progress
    def progress_hook(d):
        global progress
        if d['status'] == 'downloading':
            # Calculate progress percentage based on downloaded bytes
            progress = d.get('downloaded_bytes', 0) / d.get('total_bytes', 1) * 100
        elif d['status'] == 'finished':
            # Set progress to 100% when download is complete
            progress = 100

    # Create output directory if it doesn't exist
    output_path = os.path.join("downloaders")
    if not os.path.exists(output_path):
        os.makedirs(output_path)

    # Configure youtube-dl options
    ydl_opts = {
        'format': 'best',  # Select best quality format
        'outtmpl': os.path.join(output_path, '%(title)s.%(ext)s'),  # Set output template
        'progress_hooks': [progress_hook],  # Add progress tracking hook
    }

    # Download the video using youtube-dl
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

# Route for the main page
@app.route('/')
def index():
    # Return HTML template with embedded JavaScript
    return """
    <!DOCTYPE html>
    <html lang=\"en\">
    <head>
        <meta charset=\"UTF-8\">
        <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">
        <title>Mekawy YT Downloads</title>
        <script src=\"https://cdn.tailwindcss.com\"></script>
    </head>
    <body class=\"bg-gray-100 font-sans\">
        <header class=\"bg-black text-white p-4 flex justify-between items-center\">
            <h1 class=\"text-lg font-bold\">Mekawy Downloads</h1>
        </header>
        <main class=\"p-4\">
            <form id=\"download-form\" class=\"space-y-4\">
                <div>
                    <label for=\"url\" class=\"block text-sm font-medium text-gray-700\">Video URL</label>
                    <input type=\"text\" id=\"url\" name=\"url\" class=\"mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 text-sm\">
                </div>
                <button type=\"submit\" class=\"w-full bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded\">Download</button>
            </form>
            <div class=\"mt-4 flex justify-center\">
                <div id=\"spinner\" class=\"hidden\">
                    <svg class=\"animate-spin h-8 w-8 text-blue-500\" xmlns=\"http://www.w3.org/2000/svg\" fill=\"none\" viewBox=\"0 0 24 24\">
                        <circle class=\"opacity-25\" cx=\"12\" cy=\"12\" r=\"10\" stroke=\"currentColor\" stroke-width=\"4\"></circle>
                        <path class=\"opacity-75\" fill=\"currentColor\" d=\"M4 12a8 8 0 018-8v8h8a8 8 0 01-8 8v-8H4z\"></path>
                    </svg>
                </div>
            </div>
        </main>
        <footer class=\"bg-black text-white p-4 text-center\">
            HUSSIEN MEKAWY © 2024
        </footer>
        <script>
            // Add event listener for form submission
            document.getElementById('download-form').addEventListener('submit', async function(event) {
                event.preventDefault();
                const url = document.getElementById('url').value;
                const spinner = document.getElementById('spinner');
                spinner.classList.remove('hidden');

                // Send download request to server
                const response = await fetch('/download', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ url }),
                });

                if (response.ok) {
                    // Poll progress endpoint every 500ms
                    const interval = setInterval(async () => {
                        const progressResponse = await fetch('/progress');
                        const progressData = await progressResponse.json();

                        // Check if download is complete
                        if (progressData.progress >= 100) {
                            clearInterval(interval);
                            spinner.classList.add('hidden');
                            alert('Download Complete!');
                        }
                    }, 500);
                } else {
                    spinner.classList.add('hidden');
                    alert('Failed to start download.');
                }
            });
        </script>
    </body>
    </html>
    """

# Route to handle download requests
@app.route('/download', methods=['POST'])
def download():
    global progress
    data = request.get_json()
    url = data['url']

    # Start download in a separate thread to prevent blocking
    download_thread = threading.Thread(target=download_video, args=(url,))
    download_thread.start()

    return jsonify({"status": "started"})

# Route to get current download progress
@app.route('/progress', methods=['GET'])
def get_progress():
    return jsonify({"progress": progress})

# Run the Flask application in debug mode
if __name__ == "__main__":
    app.run(debug=True)
