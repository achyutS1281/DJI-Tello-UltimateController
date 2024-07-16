import threading

from djitellopy import Tello
from pynput.keyboard import Key, Listener
import cv2


class TelloKeyboardController:
    def __init__(self, tello: Tello):
        self.thread = None
        self.drone = tello
        self.running = False
        self.left_right = 0
        self.up_down = 0
        self.forward_back = 0
        self.yaw = 0

    def start(self):


        def on_press(InputKey):
            try:
                key = InputKey.char
                if key == 'w':
                    self.forward_back = 30
                elif key == 's':
                    self.forward_back = -30
                elif key == 'a':
                    self.left_right = -25
                elif key == 'd':
                    self.left_right = 25
                elif key == 'u':
                    self.drone.flip('f')
                elif key == 'j':
                    self.drone.flip('b')
                elif key == 'h':
                    self.drone.flip('l')
                elif key == 'l':
                    self.drone.flip('r')
                elif key == 't':
                    self.drone.set_speed(50)
                elif key == 'g':
                    self.drone.set_speed(20)
                elif key == 'f':
                    self.drone.set_speed(30)
                elif key == 'q':
                    self.drone.land()
                elif key == 'b':
                    print(self.drone.get_battery())
                elif key == 'v':
                    print(self.drone.get_height())
                elif key == '2':
                    print(self.drone.get_speed())
                elif key == '3':
                    print(self.drone.get_barometer())
                elif key == '4':
                    frame = self.drone.get_frame_read().frame
                    frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                    cv2.imwrite("/pictures/img_reg.png", frame)
                elif key == '5':
                    for i in range(12):
                        self.drone.rotate_clockwise(30)
                        cv2.waitKey(1)
                        frame = self.drone.get_frame_read().frame
                        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                        cv2.imwrite("img_pano{}.png".format(i + 1), frame)
                        cv2.waitKey(100)
                    img1 = cv2.imread("img_pano1.png")
                    img2 = cv2.imread("img_pano2.png")
                    img3 = cv2.imread("img_pano3.png")
                    img4 = cv2.imread("img_pano4.png")
                    img5 = cv2.imread("img_pano5.png")
                    img6 = cv2.imread("img_pano6.png")
                    img7 = cv2.imread("img_pano7.png")
                    img8 = cv2.imread("img_pano8.png")
                    img9 = cv2.imread("img_pano9.png")
                    img10 = cv2.imread("img_pano10.png")
                    img11 = cv2.imread("img_pano11.png")
                    img12 = cv2.imread("img_pano12.png")
                    stitcher = cv2.Stitcher.create()
                    status, stitched_image = stitcher.stitch(
                        [img1, img2, img3, img4, img5, img6, img7, img8, img9, img10, img11, img12])
                    if status == cv2.Stitcher_OK:
                        cv2.imwrite("pano_result.png", stitched_image)
                    else:
                        print("Stitch failed")

            except AttributeError:
                if InputKey == Key.up:
                    self.up_down = 25
                elif InputKey == Key.down:
                    self.up_down = -25
                elif InputKey == Key.left:
                    self.yaw = -25
                elif InputKey == Key.right:
                    self.yaw = 25
                elif InputKey == Key.space:
                    self.drone.takeoff()
            self.drone.send_rc_control(self.left_right, self.forward_back, self.up_down, self.yaw)

        def on_release(key):
            print('{0} released'.format(
                key))
            if key == Key.esc:
                self.drone.land()
                return False
            try:
                key = key.char
                if key == 'w':
                    self.forward_back = 0
                elif key == 's':
                    self.forward_back = 0
                elif key == 'a':
                    self.left_right = 0
                elif key == 'd':
                    self.left_right = 0
            except AttributeError:
                if key == Key.up:
                    self.up_down = 0
                elif key == Key.down:
                    self.up_down = 0
                elif key == Key.left:
                    self.yaw = 0
                elif key == Key.right:
                    self.yaw = 0
            self.drone.send_rc_control(self.left_right, self.forward_back, self.up_down, self.yaw)

        def begin():
            if not self.running and not (not self.thread is None and self.thread.is_alive()):
                with Listener(on_press=on_press, on_release=on_release) as listener:
                    self.thread = listener
                    self.running = True
                    listener.join()

        threading.Thread(target=begin).start()

    def stop(self):
        if self.running:
            self.thread.stop()
            self.running = False
