# Eyesu

## Overview

Eyesu is a spinoff of the reaction based game osu! where instead of the user using their cursor to go to the circles, they use their head movements to move their crosshair, and space to "hit" the targets.

## Features

- Eye tracking for cursor movement
- Automatic calibration system
- Score and combo tracking
- Visual feedback for hit accuracy (Perfect, Great, OK, Meh, Miss)
- Multiple circles can appear simultaneously
- Clean visual interface with feedback messages

## Requirements

- Python 3.x
- OpenCV (`cv2`)
- MediaPipe
- NumPy
- A webcam or camera connected to your computer

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

1. Launch the game and press any key to start calibration.
2. During calibration, keep your head still and look straight at the camera.
3. The system will calibrate based on your eye position for about 60 frames.

### Controls

- **Eye Movement**: Move your eyes to control the cursor on the screen
- **Spacebar**: Click to hit circles
- **Close Both Eyes** (for approximately 1 second): Exit the game
- **Q key**: Quit the game

### Gameplay

1. Circles will appear randomly on the screen.
2. Move your gaze to position the cursor over the circles.
3. Press the spacebar when the approach circle aligns with the main circle.
4. Your score depends on timing:
   - **PERFECT**: +300 points (extremely precise timing)
   - **GREAT**: +200 points (very good timing)
   - **OK**: +100 points (decent timing)
   - **MEH**: +50 points (poor timing)
   - **MISS**: -100 points (circle disappeared without being clicked)
5. Your combo increases with each successful hit and resets to 0 when you miss.

## Technical Details

- Uses MediaPipe's Face Mesh for precise eye tracking
- Tracks iris position relative to calibrated center point
- Applies smoothing to cursor movement for better usability
- Implements a scoring system based on timing accuracy
- Features visual feedback messages for hit quality

## Tips

- Make sure you have adequate lighting for better face detection.
- Calibrate in a comfortable position that you can maintain while playing.
- Adjust your distance from the camera for optimal tracking.
- The game works best when your face is fully visible and well-lit.

## Troubleshooting

- If eye tracking seems inaccurate, try recalibrating by restarting the game.
- Ensure your webcam has a clear view of your face.
- If the game runs slowly, close other resource-intensive applications.
- Adjust the `EYE_MOVEMENT_MULTIPLIER` constant in the code if cursor movement is too sensitive or not sensitive enough.

## Customization

You can modify various game parameters in the code:

- `CIRCLE_RADIUS`: Size of the hit circles
- `CIRCLE_LIFETIME`: How long circles remain on screen
- `MAX_CIRCLES`: Maximum number of circles that can appear simultaneously
- `EYE_MOVEMENT_MULTIPLIER`: Sensitivity of eye tracking
- Scoring windows and point values

## License

This project is provided as open-source software. Feel free to modify and distribute it according to your needs.

## Acknowledgments

- Inspired by the original OSU! rhythm game
- Uses MediaPipe for face tracking technology
- Built with Python and OpenCV
