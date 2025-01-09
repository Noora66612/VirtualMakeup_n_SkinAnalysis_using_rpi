# Virtual Makeup Website with Skin Analysis

## Introduction
This tutorial will guide you through building a Virtual Makeup Website using Python for backend processing. This application allows users to virtually apply makeup and analyze their skin in real-time using their device cameras. By following this step-by-step guide, you will learn to implement and run the project on a Raspberry Pi.

## Project Overview
- **Objective**: To create a virtual makeup application that leverages real-time video processing and OpenCV for makeup application.
- **Features**:
  - Real-time virtual makeup application.
  - Skin analysis using Mediapipe and custom logic.
- **Tools**:
  - Hardware: Raspberry Pi, MacBook (or other development devices).
  - Software: Python, OpenCV, Mediapipe, Numpy, Skinmage, Flask, Ngrok.

---

## Screenshots
![](sample/screenshot2.png)
![](sample/screenshot3.png)
![](sample/screenshot4.png)
![](sample/screenshot5.png)

## Features
- ***Real-Time Virtual Makeup Application***:

  The application allows users to try on makeup virtually in real-time using the build-in camera on their devices. The project applies makeup effects such as lip color, eyeshadow, eyeliner, and eyebrow styling to the user's face based on facial landmarks detected via the camera.
- ***Cross-Platform Access***:

  By using ngrok to expose the application, users can access the project from any device with an internet connection, even if they are not on the same network or domain. This feature ensures remote access to the application for testing or usage purposes.
- ***Customizable Makeup Styles***:

  Users can choose from different makeup styles, including Natural, Dramatic, Sweet, and Party. Each style is defined by a set of colors and opacity levels for various face elements (lips, eyes, eyebrows, etc.).
- ***Facial Landmark Detection***:

  Using MediaPipe Face Mesh, the application detects key facial landmarks (e.g. eyes, lips, cheeks) to accurately apply makeup to specific regions. The system uses a high-precision face mesh model to ensure that the makeup is aligned with the user's facial features.
- ***Face Validation***:

  The system validates if a face is properly detected, checking for conditions like face size, position, and aspect ratio. If the face is not in a valid position or is too small, users will receive feedback and a debug image for troubleshooting.
- ***Skin Analysis***:

  The system performs analysis of the user's skin to assess:
  - **Dark Circles**: Using color analysis in the LAB color space to measure the darkness under the eyes.
  - **Wrinkles**: Using multi-scale edge detection techniques to identify wrinkles in the forehead and around the eyes.
  - **Skin Tone Uniformity**: Analyzing color variations on the cheeks and forehead to determine the uniformity of the skin tone. 

## Materials and Tools
### Hardware:
- Raspberry Pi (preferably 4B or later).
- Any device equipped with a camera and capable of connecting to the internet

### Software:
- Python 3.7
- OpenCV
- Flask (for backend)
- Mediapipe
- Numpy
- Skinmage
- Ngrok (for public access)

---

## System Architecture
### Diagram
```
+----------------+        +----------------+           +----------------+
| User's Camera  | ---->  |    Frontend    | --------> |     ngrok      |
+----------------+        +----------------+           +----------------+
        |                          |                            |
        v                          v                            v
+----------------+        +--------------------+    +----------------+
| Backend Server | <----> | OpenCV + Mediapipe |    | Secure Tunnel  |
| (Python Flask) |        | Processing         |    |                |
+----------------+        +--------------------+    +----------------+

```

---

## Step-by-Step Implementation

### Setting Up the Environment
#### On the Raspberry Pi:
1. Update and upgrade the system:
   ```bash
   sudo apt update && sudo apt upgrade
   ```
2. Install Python and pip:
   ```bash
   sudo apt install python3.7 python3-pip
   ```
3. Install required libraries:
   ```bash
   pip3 install opencv-python flask mediapipe numpy scikit-image
   ```
4. Clone the project repository:
   ```bash
   git clone https://github.com/Noora66612/VirtualMakeup_n_SkinAnalysis_using_rpi.git
   cd virtual-makeup-project
   ```
### Setting Up Ngrok
#### On your device:
1. Sigh up and install Ngrok from https://ngrok.com/.

   - use a MacBook as an example
   ![](sample/ngrok_installation.png)
3. Start Ngrok to expose the Flask server:
   ```bash
   ngrok http http://localhost:5000
   ```
   
---

### Testing and Debugging
- Run the backend server on the Raspberry Pi terminal:
  ```bash
  python3 app.py
  ```
- Use Ngrok to share the application (in another terminal window on the Raspberry Pi):
  ```bash
  ngrok http http://localhost:5000
  ```
  ![](sample/screenshot8.png)
- Paste the URL into the browser on your device and ensure the camera streams correctly.
  
---

## Demo Video
- https://youtu.be/5BYBEP4fRqY
- :warning: The file name shown in the video is app3.py, but it has been corrected to app.py. Please use app.py in your setup.

---

### Personalization Options
#### Flask Backend Code (Python):
- **Modify Facial Landmark Regions**
  - The REGIONS dictionary defines facial regions based on landmark indices. You can adjust these regions by adding, removing, or redefining landmarks to better suit specific needs.
  ```python
  # Define facial landmark regions
  REGIONS = {
      'left_eye': [33, 133, 157, 158, 159, 160, 161, 173, 246],
      'right_eye': [362, 263, 249, 390, 373, 374, 380, 381, 382, 384],
      'forehead': [67, 109, 10, 338, 297, 332],
      'cheeks': [187, 411, 117, 346, 123, 147, 213, 192, 214],
  }
  ```
- **Add or Adjust Makeup Styles**
  - The MAKEUP_STYLES dictionary contains predefined styles that you can modify or expand with new options.
  ```python
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
      ...
  ```
- **Addjust Face Verification**
  - Face Size Thresholds
    - The conditions for face width and height being "too small" or "too large" can be adjusted to fine-tune detection sensitivity.
  ```python
  face_width > width * 0.1 and face_height > height * 0.1  # Face too small
  face_width < width * 0.9 and face_height < height * 0.9  # Face too large
  ```
  - Horizontal Face Centering
    - The tolerance for how centered the face must be horizontally can be customized.
  ```python
  abs((x_min + x_max)/2 - width/2) < width * 0.3  # Face not centered horizontally
  ```
  - Vertical Face Position
    - The vertical bounds for valid face placement can be tweaked.
  ```python
  y_min > height * 0.1 and y_max < height * 0.9  # Face position invalid vertically
  ```
  - Face Aspect Ratio
    - The acceptable range for the face width-to-height ratio can be modified.
  ```python
  0.5 < face_width/face_height < 2.0  # Face aspect ratio invalid
  ```
- **Addjust Skin Analysis Functions (Using Dark Circle Analysis as an Example)**
  - The analyze_dark_circles function evaluates the severity of dark circles under the eyes by analyzing brightness levels in the LAB color space. It calculates a score based on the average brightness difference in the regions below the eyes and normalizes the result.
  - Adjust Eye Region Dimensions
    - The region under each eye is extended downward by 20 pixels using:
  ```python
  y2 = min(height, y2 + 20)
  ```
  - Change Brightness Reference
    - The calculation for darkness_score compares the region's brightness to 70:
  ```python
  darkness_score = abs(70 - mean_brightness)
  ```
  - Modify Normalization Factor
   - The score normalization is controlled by:
  ```python
  normalized_score = max(0, min(100, 100 - (avg_darkness * 2)))
  ```
  - Customize Score Range
   - The score range is clamped between 20 and 95:
  ```python
  if normalized_score > 95:
    normalized_score = 95
  if normalized_score < 20:
    normalized_score = 20
  ```
  - Include Additional Features
    - Add more facial regions or adjust the eye_regions list:
  ```python
  eye_regions = ['left_eye', 'right_eye', 'eye_bags']
  ```
- **Adjust Score Thresholds and Calculate Overall Skin Analysis Scores**
  - You can modify the numeric thresholds to change what score range corresponds to each severity level.
  ```python
  def get_severity_level(score):
    """
    Convert numeric score to severity level
    """
    if score >= 85:  # Change this threshold for "Excellent"
        return 'Excellent'
    elif score >= 70:  # Change this threshold for "Good"
        return 'Good'
    elif score >= 50:  # Change this threshold for "Fair"
        return 'Fair'
    else:
        return 'Needs Improvement'  # Below 50 is considered "Needs Improvement"
  ```
  - You can change the weights in the weights dictionary for each factor (dark_circles, wrinkles, skin_tone) to reflect the relative importance of each in the overall score calculation.
  ```python
  def calculate_overall_score(analysis):
    """
    Calculate weighted average of all skin analysis scores
    """
    weights = {
        'dark_circles': 0.3,  # Change this weight for dark circles
        'wrinkles': 0.3,      # Change this weight for wrinkles
        'skin_tone': 0.4      # Change this weight for skin tone
    }
    ...
  ```
---

###  Developing the Frontend
#### HTML and JavaScript:
- **Addjusting Resolutoin**
  - You can modify the width, height, and frameRate to suit different needs. 
```html
 stream = await navigator.mediaDevices.getUserMedia({
  video: {
    facingMode: 'user',
    width: { ideal: 1280 },
    height: { ideal: 720 }
         }
  });
```
- **Adding Makeup Style Switches**
  - You can add more style buttons by adding more key-value pairs to the styleButtons object.
```html
// Makeup style buttons
  const styleButtons = {
    natural: document.getElementById('naturalButton'),
    dramatic: document.getElementById('dramaticButton'),
    sweet: document.getElementById('sweetButton'),
    party: document.getElementById('partyButton')
  };
```
---

## Areas for Improvement and Suggestions
- ***Video Latency***
  - **Issue**:

    The application exhibits noticeable video latency during real-time processing, particularly on low-performance devices such as the Raspberry Pi.
  - **Suggestions for Improvement**:

    - Optimize Video Processing: Utilize techniques like hardware acceleration (e.g., leveraging WebGL or GPU processing) to reduce the computational load.
    - Adjust Resolution: Allow users to select lower video resolutions to decrease processing time.
    - Asynchronous Processing: Introduce asynchronous or multithreaded processing to improve the responsiveness of the application.

- ***Unrealistic Skin Analysis Scores***
  - **Issue**:
    
    The skin analysis scores provided by the application sometimes do not align with real-world conditions, leading to user dissatisfaction.
  - **Suggestions for Improvement**:
    - Enhance Model Training: Use a larger, more diverse dataset to train the machine learning models for skin analysis.
    - Validation Mechanisms: Incorporate additional checks or calibrations to improve the accuracy of the scores.
    - User Feedback Integration: Allow users to rate the accuracy of the analysis, which can be used to refine the system over time.

- ***Sensitivity to Lighting Conditions***
  - **Issue**:

    The accuracy of the skin analysis is significantly affected by variations in lighting conditions, which impacts the reliability of the results.

  - **Suggestions for Improvement**:
 
    - Implement Lighting Normalization: Use computer vision techniques to normalize lighting effects in the captured images.
    - Guide for Optimal Lighting: Provide users with guidance on maintaining consistent lighting (e.g., positioning near natural light sources or using neutral lighting).
    - Dynamic Adjustments: Incorporate real-time adjustments to account for lighting variations using algorithms like histogram equalization.

---

## Conclusion
By following this tutorial, you should have a functional Virtual Makeup Application running on a Raspberry Pi. However, please note that this is just a basic implementation and not the final or perfect version. We kindly ask for your understanding as there may be areas that still need improvement.

---

## References
- Flask: https://flask.palletsprojects.com/
- OpenCV: https://opencv.org/
- Mediapipe: https://google.github.io/mediapipe/
- numpy: https://numpy.org
- Skinmage: https://github.com/Tobias-Fischer/skinmage
- ngrok: https://ngrok.com/
- Python 3.7: https://www.python.org/
- Threading in Python: https://docs.python.org/3/library/threading.html
- Local Binary Pattern (LBP): https://en.wikipedia.org/wiki/Local_binary_pattern

- virtual makeup using mediapipe on github
  - https://github.com/Jayanths9/Virtual_Makeup

- OpenAI ChatGPT: 
ChatGPT was utilized during the development process for brainstorming ideas, writing documentation, and debugging assistance.
  - https://chatgpt.com
- Anthropic Claude: 
Claude was used to refine the project's documentation and assist in technical problem-solving
  - https://claude.ai

