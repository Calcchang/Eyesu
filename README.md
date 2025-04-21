# Eyesu

## Overview

Eyesu is a spinoff of the reaction based game osu! where instead of the user using their cursor to go to the circles, they use their head movements to move their crosshair, and space to "hit" the targets.

## Features

- Eye tracking for crosshair movement
- Initial calibration system
- Score and combo tracking
- Visual feedback for hit accuracy (Perfect, Great, OK, Meh, Miss)
- CIRCLES!!!!

## Requirements

- Python 3.x
- OpenCV (`cv2`)
- MediaPipe
- NumPy
- A webcam or a externally connected camera

## Installation

1. Install the required Python packages:

```bash
pip install opencv-python mediapipe numpy
```

2. Clone or download this repository to your local machine.

3. Run the game:

```bash
python eye_controlled_osu.py
```

## How to Play

### Setup and Calibration

1. Launch the game and DON'T MOVE YOUR HEAD UNTIL CALIBRATION IS COMPLETE.
2. During calibration, keep your head still and look straight at the camera.
3. The system will calibrate based on your eye position for about 60 frames.

### Controls

- **Eye Movement**: Move your eyes to control the cursor on the screen
- **Spacebar**: Click to hit circles
- **Q key**: Quit the game

### Gameplay

1. Circles will appear randomly on the screen.
2. Move your gaze to position the cursor over the circles.
3. Press the spacebar when the outer ring and the circle seem to intersect
4. Your score depends on timing:
   - **PERFECT**: +300 points (very precise timing)
   - **GREAT**: +200 points (good timing)
   - **OK**: +100 points (decent timing)
   - **MEH**: +50 points (mid timing)
   - **MISS**: -100 points (circle disappeared without being clicked)
5. Your combo is similar to your hit streak, if you miss a circle then your combo resets to 0

## Tips

- Make sure you have good lighting for better face detection.
- Calibrate in a comfortable position and ensure your head is centered in the frame
- Adjust your distance from the camera for optimal tracking. (Most normal sitting distances should be fine)

## Troubleshooting

- Try recalibrating by restarting the game if the crosshair seems off or miscentered
- Adjust the `EYE_MOVEMENT_MULTIPLIER` constant in the code if cursor movement is too sensitive or not sensitive enough. (I hardcoded it to my specific window size)

## Customization

You can modify these game parameters in the code for customization:

- `CIRCLE_RADIUS`: Size of the hit circles
- `CIRCLE_LIFETIME`: How long circles remain on screen
- `MAX_CIRCLES`: Maximum number of circles that can appear simultaneously
- `EYE_MOVEMENT_MULTIPLIER`: Sensitivity of eye tracking
- Scoring windows and point values

## Credits

- Inspired by the original OSU! rhythm game
- Uses MediaPipe for face tracking technology
- Built with Python and OpenCV
