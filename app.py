from flask import Flask, render_template
import os
import shutil
import psutil
import time
from PIL import Image
app = Flask(__name__)

STORAGE = "/mnt/storage"


def get_temperature():
    try:
        with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
            return round(int(f.read()) / 1000, 1)
    except:
        return "N/A"


def format_uptime(seconds):
    days = int(seconds // 86400)
    hours = int((seconds % 86400) // 3600)
    minutes = int((seconds % 3600) // 60)

    if days:
        return f"{days}d {hours}h"
    elif hours:
        return f"{hours}h {minutes}m"
    else:
        return f"{minutes}m"
def create_thumbnail(image_path):
    try:
        thumb_folder = "/home/josue/nas-dashboard/thumbnails"

        os.makedirs(thumb_folder, exist_ok=True)

        filename = os.path.basename(image_path)
        thumb_path = os.path.join(
            thumb_folder,
            filename
        )

        # Don't recreate thumbnails that already exist
        if os.path.exists(thumb_path):
            return thumb_path

        img = Image.open(image_path)
        img.thumbnail((300, 300))

        img.save(thumb_path)

        return thumb_path

    except Exception:
        return None

@app.route("/")
def home():
    total, used, free = shutil.disk_usage(STORAGE)

    storage = {
        "total": round(total / (1024**3), 1),
        "used": round(used / (1024**3), 1),
        "percent": round((used / total) * 100, 1),
    }

    folders = []

    for folder in sorted(os.listdir(STORAGE)):
        full_path = os.path.join(STORAGE, folder)

        if not folder.startswith(".") and os.path.isdir(full_path):
            folders.append(folder)

    return render_template(
        "index.html",
        storage=storage,
        folders=folders,
        cpu=psutil.cpu_percent(),
        temp=get_temperature(),
        uptime=format_uptime(time.time() - psutil.boot_time()),
    )


@app.route("/folder/<path:name>")
def folder(name):
    path = os.path.join(STORAGE, name)

    if not os.path.exists(path):
        return "Folder not found"

    items = []

    for item in sorted(os.listdir(path)):
        full_path = os.path.join(path, item)

        if os.path.isdir(full_path):
            icon = "📁"
            size = ""
        else:
            icon = "📄"
            size_bytes = os.path.getsize(full_path)

            if size_bytes < 1024:
                size = f"{size_bytes} B"
            elif size_bytes < 1024**2:
                size = f"{size_bytes / 1024:.1f} KB"
            elif size_bytes < 1024**3:
                size = f"{size_bytes / (1024**2):.1f} MB"
            else:
                size = f"{size_bytes / (1024**3):.1f} GB"

        items.append({
            "name": item,
            "icon": icon,
            "size": size,
        })

    return render_template(
        "folder.html",
        folder=name,
        files=items,
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
