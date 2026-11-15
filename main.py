
from pathlib import Path
from urllib.parse import urlparse
import uuid

from flask import Flask, render_template, request, send_file, flash, redirect, url_for
import yt_dlp

app = Flask(__name__)
app.secret_key = "change-this-secret-key"

BASE_DIR = Path(__file__).resolve().parent
DOWNLOAD_DIR = BASE_DIR / "downloads"
DOWNLOAD_DIR.mkdir(exist_ok=True)

ALLOWED_HOSTS = {
    "tiktok.com",
    "www.tiktok.com",
    "m.tiktok.com",
    "vm.tiktok.com",
    "vt.tiktok.com"
}


def valid_tiktok_url(url):
    try:
        parsed = urlparse(url.strip())
        host = (parsed.hostname or "").lower()

        return (
            parsed.scheme in ("http", "https")
            and (
                host in ALLOWED_HOSTS
                or host.endswith(".tiktok.com")
            )
        )
    except ValueError:
        return False


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        video_url = request.form.get("video_url", "").strip()

        if not valid_tiktok_url(video_url):
            flash("Please enter a valid TikTok link.", "error")
            return redirect(url_for("index"))

        job_id = uuid.uuid4().hex

        options = {
            "format": "best[ext=mp4]/best",
            "outtmpl": str(DOWNLOAD_DIR / f"{job_id}.%(ext)s"),
            "noplaylist": True,
            "quiet": True,
            "no_warnings": True
        }

        try:
            with yt_dlp.YoutubeDL(options) as downloader:
                info = downloader.extract_info(
                    video_url,
                    download=True
                )
                file_path = Path(
                    downloader.prepare_filename(info)
                )

            if not file_path.exists():
                candidates = list(DOWNLOAD_DIR.glob(f"{job_id}.*"))
                if not candidates:
                    raise FileNotFoundError()
                file_path = candidates[0]

            return send_file(
                file_path,
                as_attachment=True,
                download_name=f"tiktok_{job_id[:8]}{file_path.suffix}"
            )

        except Exception:
            flash("Download failed. Check the link and try again.", "error")
            return redirect(url_for("index"))

    return render_template("index.html")


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
