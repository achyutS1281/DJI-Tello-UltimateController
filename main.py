#!/usr/bin/env python
# -*- coding: utf-8 -*-
import configargparse

import cv2 as cv
from Controllers.gesture_recognition import GestureRecognition, GestureBuffer
from Controllers.tello_keyboard_controller import TelloKeyboardController
from Controllers.tello_gesture_controller import TelloGestureController
from utils.cvfpscalc import CvFpsCalc
from Controllers.tello_speech_controller import Speech_Controller

from djitellopy import Tello
from Controllers import *

import threading


def get_args():
    print('## Reading configuration ##')
    parser = configargparse.ArgParser(default_config_files=['config.txt'])

    parser.add_argument('-c', '--my-config', required=False, is_config_file=True, help='config file path')
    parser.add_argument("--device", type=int)
    parser.add_argument("--width", help='cap width', type=int)
    parser.add_argument("--height", help='cap height', type=int)
    parser.add_argument("--is_keyboard", help='To use Keyboard control by default', type=bool)
    parser.add_argument('--use_static_image_mode', action='store_true', help='True if running on photos')
    parser.add_argument("--min_detection_confidence",
                        help='min_detection_confidence',
                        type=float)
    parser.add_argument("--min_tracking_confidence",
                        help='min_tracking_confidence',
                        type=float)
    parser.add_argument("--buffer_len",
                        help='Length of gesture buffer',
                        type=int)

    args = parser.parse_args()

    return args


def select_mode(key, mode):
    number = -1
    if 48 <= key <= 57:  # 0 ~ 9
        number = key - 48
    if key == 110:  # n
        mode = 0
    if key == 107:  # k
        mode = 1
    if key == 104:  # h
        mode = 2
    return number, mode


def main():
    # init global vars
    global gesture_buffer
    global gesture_id
    global battery_status
    global pause
    global in_flight
    # Argument parsing
    args = get_args()
    KEYBOARD_CONTROL = args.is_keyboard
    SPEECH_CONTROL = False
    OBJECT_CONTROL = False
    WRITE_CONTROL = False
    in_flight = False
    pause = False
    # Camera preparation
    tello = Tello()
    tello.connect()
    tello.streamon()

    cap = tello.get_frame_read()

    # Init Tello Controllers
    gesture_controller = TelloGestureController(tello)
    keyboard_controller = TelloKeyboardController(tello)
    speech_controller = Speech_Controller(tello)
    gesture_detector = GestureRecognition(args.use_static_image_mode, args.min_detection_confidence,
                                          args.min_tracking_confidence)
    gesture_buffer = GestureBuffer(buffer_len=args.buffer_len)

    def takeoff():
        global pause
        global in_flight
        pause = True
        tello.takeoff()
        in_flight = True
        pause = False

    def land():
        global pause
        global in_flight
        pause = True
        tello.land()
        in_flight = False
        pause = False


    def tello_control(key, keyboard_controller, gesture_controller):
        global gesture_buffer

        if not KEYBOARD_CONTROL and not SPEECH_CONTROL and not OBJECT_CONTROL:
            gesture_controller.gesture_control(gesture_buffer)

    def tello_battery(tello):
        global battery_status
        try:
            battery_status = tello.get_battery()
        except:
            battery_status = -1

    def object_recog_mode(drone, img):
        img_gray = cv.cvtColor(img, cv.COLOR_BGR2RGB)
        img_rgb = cv.cvtColor(img, cv.COLOR_BGR2RGB)

        data = cv.CascadeClassifier("haarcascade_frontalface_default.xml")
        img_height, img_width, channels = img.shape
        found = data.detectMultiScale(img_gray, minSize=(40, 40))
        max_width = 0
        max_x = 0
        max_y = 0
        max_height = 0
        if len(found) != 0:
            for (x, y, width, height) in found:
                if width > max_width:
                    max_width = width
                    max_x = x
                    max_y = y
                    max_height = height

                    img_rgb = cv.rectangle(img_rgb, (x, y), (x + height, y + width), (0, 255, 0), 5)
            if max_width == 0:
                drone.send_rc_control(0, 0, 0, 0)
                return
            buffer_width = img_width // 10
            buffer_height = img_height // 10
            if max_x < (img_width // 2):
                left_right = -70
            elif max_x > (img_width // 2):
                left_right = 70
            else:
                left_right = 0
            # if max_y < (img_height // 2):
            #    up_down = -30
            # elif max_y > (img_height // 2):
            #    up_down = 30
            # else:
            #    up_down = 0

            drone.send_rc_control(0, 0, 0, left_right)

    # FPS Measurement
    cv_fps_calc = CvFpsCalc(buffer_len=10)

    mode = 0
    number = -1
    battery_status = -1
    scale = 1

    while True:
        fps = cv_fps_calc.get()

        # Process Key (ESC: end)
        key = cv.waitKey(1) & 0xff
        if key == 27:  # ESC
            break
        elif key == 32:  # Space
            if not in_flight:
                # Take-off drone
                threading.Thread(target=takeoff).start()

            elif in_flight:
                # Land tello
                threading.Thread(target=land).start()

        elif key == ord('k'):
            mode = 0
            KEYBOARD_CONTROL = True
            WRITE_CONTROL = False
            SPEECH_CONTROL = False
            OBJECT_CONTROL = False
            tello.send_rc_control(0, 0, 0, 0)  # Stop moving
            keyboard_controller.stop()
            keyboard_controller.start()
            keyboard_controller.start()
            speech_controller.stop()
        elif key == ord('g'):
            SPEECH_CONTROL = False
            KEYBOARD_CONTROL = False
            OBJECT_CONTROL = False
            keyboard_controller.stop()
            speech_controller.stop()
        elif key == ord('n'):
            mode = 1
            WRITE_CONTROL = True
            KEYBOARD_CONTROL = True
            SPEECH_CONTROL = False
            OBJECT_CONTROL = False
            keyboard_controller.start()
            speech_controller.stop()
        elif key == ord('.'):
            SPEECH_CONTROL = True
            KEYBOARD_CONTROL = False
            OBJECT_CONTROL = False
            keyboard_controller.stop()
            speech_controller.start()
        elif key == ord(','):
            SPEECH_CONTROL = False
            KEYBOARD_CONTROL = False
            OBJECT_CONTROL = True
            keyboard_controller.stop()
            speech_controller.stop()
        if WRITE_CONTROL:
            number = -1
            if 48 <= key <= 57:  # 0 ~ 9
                number = key - 48

        # Camera capture
        image = cap.frame

        debug_image, gesture_id = gesture_detector.recognize(image, number, mode)
        gesture_buffer.add_gesture(gesture_id)

        # Start control thread
        if not pause:
            threading.Thread(target=tello_control, args=(key, keyboard_controller, gesture_controller,)).start()
        threading.Thread(target=tello_battery, args=(tello,)).start()

        debug_image = gesture_detector.draw_info(debug_image, fps, mode, number)

        # Battery status and image rendering

        height, width, channels = debug_image.shape

        # prepare the crop
        centerX, centerY = int(height / 2), int(width / 2)
        radiusX, radiusY = int(centerX * scale), int(centerY * scale)

        minX, maxX = centerX - radiusX, centerX + radiusX
        minY, maxY = centerY - radiusY, centerY + radiusY

        cropped = debug_image[minX:maxX, minY:maxY]
        debug_image = cv.resize(cropped, (width, height))
        # add + or - 5 % to zoom
        cv.putText(debug_image, "Battery: {}".format(battery_status), (5, 720 - 5),
                   cv.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        cv.imshow('Ultimate Tello Controller', debug_image)
        if key == ord('-') and scale <= 0.95:
            scale += 0.05  # +5

        if key == ord('=') and scale >= 0.06:
            scale -= 0.05  # +5

        if key == ord('o'):
            scale = 1

    tello.land()
    tello.end()
    cv.destroyAllWindows()


if __name__ == '__main__':
    main()
