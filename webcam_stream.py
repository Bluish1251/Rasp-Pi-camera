import cv2
import numpy as np
from flask import Flask, Response, render_template_string
from picamera2 import Picamera2

app = Flask(__name__)
picam2 = Picamera2()
picam2.configure(picam2.create_preview_configuration(main={"size": (640, 480)}))
picam2.start()

# Browser Stuff
HTML_PAGE = """
<html>
<head>
    <title>Live Camera Filters</title>
</head>
<body style="background-color: #111; color: white; text-align: center;">
    <h1> Live Camera with Filters</h1>
    <div style="display: flex; flex-wrap: wrap; justify-content: center;">
        <div><h3>Original</h3><img src="/video/original"></div>
        <div><h3>Grayscale</h3><img src="/video/gray"></div>
        <div><h3>Blurred</h3><img src="/video/blur"></div>
        <div><h3>Edges</h3><img src="/video/canny"></div>
        <div><h3>Dilated</h3><img src="/video/dilate"></div>
        <div><h3>Eroded</h3><img src="/video/erode"></div>
    </div>
</body>
</html>
"""

# Filters
def apply_filter(frame, filter_type):
    kernel = np.ones((5,5), np.uint8)
    if filter_type == "gray":
        return cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    elif filter_type == "blur":
        return cv2.GaussianBlur(frame, (11,11), 0)
    elif filter_type == "canny":
        return cv2.Canny(frame, 100, 100)
    elif filter_type == "dilate":
        edge = cv2.Canny(frame, 100, 100)
        return cv2.dilate(edge, kernel, iterations=1)
    elif filter_type == "erode":
        edge = cv2.Canny(frame, 100, 100)
        dilated = cv2.dilate(edge, kernel, iterations=1)
        return cv2.erode(dilated, kernel, iterations=1)
    else:  # original
        return frame

# Streaming 
def generate(filter_type):
    while True:
        frame = picam2.capture_array()
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        filtered = apply_filter(frame, filter_type)
        if len(filtered.shape) == 2:  # grayscale or single-channel
            filtered = cv2.cvtColor(filtered, cv2.COLOR_GRAY2RGB)
        _, buffer = cv2.imencode('.jpg', filtered)
        frame_bytes = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

@app.route("/")
def index():
    return render_template_string(HTML_PAGE)

@app.route("/video/<filter_type>")
def video_feed(filter_type):
    return Response(generate(filter_type),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
