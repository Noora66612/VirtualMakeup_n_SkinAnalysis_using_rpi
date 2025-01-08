from flask import Flask, render_template, Response, request, jsonify
import cv2
import numpy as np
from utils import *
from threading import Lock
import socket
import logging
import json
import mediapipe as mp
import base64
from skimage.feature import local_binary_pattern

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = False
app.config['DEBUG'] = False

processing_lock = Lock()

# Initialize MediaPipe Face Mesh
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(
    max_num_faces=1,
    refine_landmarks=True,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

# Define facial landmark regions
REGIONS = {
    'left_eye': [33, 133, 157, 158, 159, 160, 161, 173, 246],
    'right_eye': [362, 263, 249, 390, 373, 374, 380, 381, 382],
    'forehead': [67, 109, 10, 338, 297, 332],
    'cheeks': [187, 411, 117, 346, 123, 147, 213, 192, 214],
}

# Makeup configuration
face_elements = [
    "LIP_LOWER",
    "LIP_UPPER",
    "EYEBROW_LEFT",
    "EYEBROW_RIGHT",
    "EYELINER_LEFT",
    "EYELINER_RIGHT",
    "EYESHADOW_LEFT",
    "EYESHADOW_RIGHT",
]

# Define makeup styles
MAKEUP_STYLES = {
    'natural': {
        'colors': {
            'LIP_UPPER': [0, 0, 180],
            'LIP_LOWER': [0, 0, 180],
            'EYELINER_LEFT': [90, 60, 40],
            'EYELINER_RIGHT': [90, 60, 40],
            'EYESHADOW_LEFT': [132, 89, 83],
            'EYESHADOW_RIGHT': [132, 89, 83],
            'EYEBROW_LEFT': [0, 0, 0],
            'EYEBROW_RIGHT': [0, 0, 0]
        },
        'opacity': 0.2
    },
    'dramatic': {
        'colors': {
            'LIP_UPPER': [0, 0, 255],
            'LIP_LOWER': [0, 0, 255],
            'EYELINER_LEFT': [0, 0, 0],
            'EYELINER_RIGHT': [0, 0, 0],
            'EYESHADOW_LEFT': [128, 0, 128],
            'EYESHADOW_RIGHT': [128, 0, 128],
            'EYEBROW_LEFT': [0, 0, 0],
            'EYEBROW_RIGHT': [0, 0, 0]
        },
        'opacity': 0.3
    },
    'sweet': {
        'colors': {
            'LIP_UPPER': [0, 0, 180],
            'LIP_LOWER': [0, 0, 180],
            'EYELINER_LEFT': [0, 0, 180],
            'EYELINER_RIGHT': [0, 0, 180],
            'EYESHADOW_LEFT': [180, 130, 80],
            'EYESHADOW_RIGHT': [180, 130, 80],
            'EYEBROW_LEFT': [0, 0, 0],
            'EYEBROW_RIGHT': [0, 0, 0]
        },
        'opacity': 0.25
    },
    'party': {
        'colors': {
            'LIP_UPPER': [0, 0, 128],
            'LIP_LOWER': [0, 0, 128],
            'EYELINER_LEFT': [0, 0, 0],
            'EYELINER_RIGHT': [0, 0, 0],
            'EYESHADOW_LEFT': [0, 165, 255],
            'EYESHADOW_RIGHT': [0, 165, 255],
            'EYEBROW_LEFT': [51, 51, 51],
            'EYEBROW_RIGHT': [51, 51, 51]
        },
        'opacity': 0.3
    }
}

current_style = 'natural'

def verify_face_detection(frame, landmarks):
    """
    Verify if a face is properly detected and within valid bounds
    Returns: (is_valid, debug_frame, message)
    """
    height, width = frame.shape[:2]
    debug_frame = frame.copy()
    
    if landmarks is None:
        return False, debug_frame, "No face landmarks detected"

    # Extract key facial points
    points = []
    for landmark in landmarks.landmark:
        x, y = int(landmark.x * width), int(landmark.y * height)
        points.append((x, y))
        cv2.circle(debug_frame, (x, y), 1, (0, 255, 0), -1)
    
    if not points:
        return False, debug_frame, "No valid facial points found"

    points = np.array(points)
    
    # Calculate face boundary
    x_min, y_min = points.min(axis=0)
    x_max, y_max = points.max(axis=0)
    face_width = x_max - x_min
    face_height = y_max - y_min
    
    cv2.rectangle(debug_frame, (int(x_min), int(y_min)), 
                 (int(x_max), int(y_max)), (0, 255, 0), 2)

    # Validation checks
    validations = [
        (face_width > width * 0.1 and face_height > height * 0.1,
         "Face too small"),
        (face_width < width * 0.9 and face_height < height * 0.9,
         "Face too large"),
        (abs((x_min + x_max)/2 - width/2) < width * 0.3,
         "Face not centered horizontally"),
        (y_min > height * 0.1 and y_max < height * 0.9,
         "Face position invalid vertically"),
        (0.5 < face_width/face_height < 2.0,
         "Face aspect ratio invalid")
    ]
    
    for is_valid, message in validations:
        if not is_valid:
            return False, debug_frame, message

    cv2.putText(debug_frame, "Face Verified", (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
    
    return True, debug_frame, "Face verified successfully"

def analyze_dark_circles(frame, landmarks):
    """
    Analyze dark circles under eyes using LAB color space
    """
    height, width = frame.shape[:2]
    lab = cv2.cvtColor(frame, cv2.COLOR_BGR2Lab)
    eye_regions = ['left_eye', 'right_eye']
    darkness_scores = []
    
    for region in eye_regions:
        points = REGIONS[region]
        region_landmarks = [landmarks.landmark[p] for p in points]
        x_coords = [int(l.x * width) for l in region_landmarks]
        y_coords = [int(l.y * height) for l in region_landmarks]
        x1, y1 = min(x_coords), min(y_coords)
        x2, y2 = max(x_coords), max(y_coords)
        
        # Extend the region downward
        y2 = min(height, y2 + 20)
        
        roi = lab[y1:y2, x1:x2]
        if roi.size > 0:
            l_channel = roi[:,:,0]
            mean_brightness = np.mean(l_channel)
            darkness_score = abs(70 - mean_brightness)
            darkness_scores.append(darkness_score)
    
    if not darkness_scores:
        return {
            'score': 90,
            'severity': 'Excellent'
        }
    
    avg_darkness = np.mean(darkness_scores)
    normalized_score = max(0, min(100, 100 - (avg_darkness * 2)))
    
    if normalized_score > 95:
        normalized_score = 95
    if normalized_score < 20:
        normalized_score = 20
    
    return {
        'score': round(normalized_score, 2),
        'severity': get_severity_level(normalized_score)
    }

def analyze_wrinkles(frame, landmarks):
    """
    Analyze wrinkles using multi-scale edge detection
    """
    height, width = frame.shape[:2]
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    
    # Preprocessing
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    enhanced = clahe.apply(gray)
    bilateral = cv2.bilateralFilter(enhanced, 9, 75, 75)
    
    wrinkle_scores = []
    kernels = [(3,3), (5,5), (7,7)]
    
    for region in ['forehead', 'left_eye', 'right_eye']:
        points = REGIONS[region]
        region_landmarks = [landmarks.landmark[p] for p in points]
        x_coords = [int(l.x * width) for l in region_landmarks]
        y_coords = [int(l.y * height) for l in region_landmarks]
        
        padding = 10
        x1 = max(0, min(x_coords) - padding)
        y1 = max(0, min(y_coords) - padding)
        x2 = min(width, max(x_coords) + padding)
        y2 = min(height, max(y_coords) + padding)
        
        roi = bilateral[y1:y2, x1:x2]
        if roi.size > 0:
            region_scores = []
            
            for ksize in kernels:
                edges = cv2.Canny(roi, 30, 80)
                score = np.sum(edges > 0) / roi.size
                region_scores.append(score)
            
            wrinkle_scores.append(max(region_scores))
    
    if not wrinkle_scores:
        return {
            'score': 95,
            'severity': 'Excellent'
        }
    
    avg_wrinkle = np.mean(wrinkle_scores)
    normalized_score = max(0, min(100, 100 - (avg_wrinkle * 1000)))
    
    if normalized_score < 20:
        normalized_score = 20
    if normalized_score > 95:
        normalized_score = 95
    
    return {
        'score': round(normalized_score, 2),
        'severity': get_severity_level(normalized_score)
    }

def analyze_skin_tone(frame, landmarks):
    """
    Analyze skin tone uniformity using LAB color space
    """
    height, width = frame.shape[:2]
    lab = cv2.cvtColor(frame, cv2.COLOR_BGR2Lab)
    
    regions_to_check = ['cheeks', 'forehead']
    uniformity_scores = []
    
    for region in regions_to_check:
        points = REGIONS[region]
        region_landmarks = [landmarks.landmark[p] for p in points]
        x_coords = [int(l.x * width) for l in region_landmarks]
        y_coords = [int(l.y * height) for l in region_landmarks]
        x1, y1 = min(x_coords), min(y_coords)
        x2, y2 = max(x_coords), max(y_coords)
        
        roi = lab[y1:y2, x1:x2]
        
        if roi.size > 0:
            std_l = np.std(roi[:,:,0])  # Brightness variation
            std_a = np.std(roi[:,:,1])  # Red-Green variation
            std_b = np.std(roi[:,:,2])  # Blue-Yellow variation
            
            uniformity = (std_l * 0.4 + std_a * 0.3 + std_b * 0.3)
            uniformity_scores.append(uniformity)
    
    if not uniformity_scores:
        return {
            'score': 90,
            'severity': 'Excellent'
        }
    
    avg_uniformity = np.mean(uniformity_scores)
    normalized_score = max(0, min(100, 100 - (avg_uniformity * 2.5)))
    
    if normalized_score > 95:
        normalized_score = 95
    if normalized_score < 20:
        normalized_score = 20
    
    return {
        'score': round(normalized_score, 2),
        'severity': get_severity_level(normalized_score)
    }

def get_severity_level(score):
    """
    Convert numeric score to severity level
    """
    if score >= 85:
        return 'Excellent'
    elif score >= 70:
        return 'Good'
    elif score >= 50:
        return 'Fair'
    else:
        return 'Needs Improvement'

def calculate_overall_score(analysis):
    """
    Calculate weighted average of all skin analysis scores
    """
    weights = {
        'dark_circles': 0.3,
        'wrinkles': 0.3,
        'skin_tone': 0.4
    }
    
    total_score = (
        analysis['dark_circles']['score'] * weights['dark_circles'] +
        analysis['wrinkles']['score'] * weights['wrinkles'] +
        analysis['skin_tone']['score'] * weights['skin_tone']
    )
    
    return round(total_score, 2)

def encode_debug_image(image):
    """
    Encode image for frontend display
    """
    _, buffer = cv2.imencode('.jpg', image)
    return 'data:image/jpeg;base64,' + base64.b64encode(buffer).decode('utf-8')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/change_style', methods=['POST'])
def change_style():
    global current_style
    data = request.get_json()
    style = data.get('style')
    if style in MAKEUP_STYLES:
        current_style = style
        return {'status': 'success'}
    return {'status': 'error', 'message': 'Invalid style'}, 400

@app.route('/analyze_skin', methods=['POST'])
def analyze_skin():
    if 'frame' not in request.files:
        return jsonify({'error': 'No frame uploaded'}), 400
        
    frame_file = request.files['frame']
    frame_bytes = frame_file.read()
    nparr = np.frombuffer(frame_bytes, np.uint8)
    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    with processing_lock:
        try:
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = face_mesh.process(rgb_frame)
            
            if not results.multi_face_landmarks:
                return jsonify({
                    'error': 'No face detected',
                    'message': 'Please ensure your face is clearly visible'
                }), 400
                
            landmarks = results.multi_face_landmarks[0]
            
            # Verify face detection
            is_valid, debug_frame, message = verify_face_detection(frame, landmarks)
            
            if not is_valid:
                return jsonify({
                    'error': 'Invalid face position',
                    'message': message,
                    'debug_image': encode_debug_image(debug_frame)
                }), 400
            
            analysis = {
                'dark_circles': analyze_dark_circles(frame, landmarks),
                'wrinkles': analyze_wrinkles(frame, landmarks),
                'skin_tone': analyze_skin_tone(frame, landmarks),
                'overall_score': 0,
                'face_position': 'valid',
                'debug_image': encode_debug_image(debug_frame)
            }
            
            analysis['overall_score'] = calculate_overall_score(analysis)
            
            return jsonify(analysis)
            
        except Exception as e:
            print(f"Error analyzing skin: {str(e)}")
            return jsonify({'error': str(e)}), 500

@app.route('/process_frame', methods=['POST'])
def process_frame():
    if 'frame' not in request.files:
        return 'No frame uploaded', 400
        
    frame_file = request.files['frame']
    frame_bytes = frame_file.read()
    nparr = np.frombuffer(frame_bytes, np.uint8)
    
    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    frame = cv2.resize(frame, (480, 360))
    
    with processing_lock:
        try:
            mask = np.zeros_like(frame)
            face_landmarks = read_landmarks(image=frame)
            
            current_colors = [MAKEUP_STYLES[current_style]['colors'][element] for element in face_elements]
            face_connections = [face_points[idx] for idx in face_elements]
            
            mask = add_mask(
                mask,
                idx_to_coordinates=face_landmarks,
                face_connections=face_connections,
                colors=current_colors
            )
            
            opacity = MAKEUP_STYLES[current_style]['opacity']
            output = cv2.addWeighted(frame, 1.0, mask, opacity, 1.0)
            
            encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 70]
            ret, buffer = cv2.imencode('.jpg', output, encode_param)
            
            response = Response(buffer.tobytes(), mimetype='image/jpeg')
            response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
            response.headers['Pragma'] = 'no-cache'
            return response
            
        except Exception as e:
            print(f"Error processing frame: {str(e)}")
            return 'Error processing frame', 500

def get_ip():
    """
    Get the server's IP address
    """
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return 'localhost'

if __name__ == '__main__':
    ip = get_ip()
    print('='*50)
    print('Starting server')
    print('='*50)
    print(f'http://{ip}:5000')
    print('='*50)
    
    try:
        from waitress import serve
        serve(app, host="0.0.0.0", port=5000, threads=4)
    except Exception as e:
        print(f'Server error: {str(e)}')

