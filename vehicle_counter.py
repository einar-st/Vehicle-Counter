import cv2
from ultralytics import YOLO
import time


# this function attempts to match the original video speed by altering the
# cv2.delay setting
def match_speed(fps, dur):

    dur_ms = int(dur * 1000)
    if dur_ms > fps:
        delay = 1
        # print('Problems matching original video speed')
    else:
        delay = int(1000 / fps - dur_ms)
    return delay


# check if x,y coordinates are within a set of boundaries
def in_box(x, y, box):
    x1, y1, x2, y2 = box
    if x > x1 and x < x2 and y > y1 and y < y2:
        return True
    return False


def draw_corners(target, xyxy, col, thickness):

    linelen = int(min(abs(xyxy[3] - xyxy[1]), (abs(xyxy[2] - xyxy[0]))) / 10)

    cv2.line(
        target, (xyxy[0], xyxy[1]), (xyxy[0] + linelen, xyxy[1]),
        col, thickness
    )
    cv2.line(
        target, (xyxy[0], xyxy[1]), (xyxy[0], xyxy[1] + linelen),
        col, thickness
    )
    cv2.line(
        target, (xyxy[2], xyxy[1]), (xyxy[2] - linelen, xyxy[1]),
        col, thickness
    )
    cv2.line(
        target, (xyxy[2], xyxy[1]), (xyxy[2], xyxy[1] + linelen),
        col, thickness
    )
    cv2.line(
        target, (xyxy[0], xyxy[3]), (xyxy[0] + linelen, xyxy[3]),
        col, thickness
    )
    cv2.line(
        target, (xyxy[0], xyxy[3]), (xyxy[0], xyxy[3] - linelen),
        col, thickness
    )
    cv2.line(
        target, (xyxy[2], xyxy[3]), (xyxy[2] - linelen, xyxy[3]),
        col, thickness
    )
    cv2.line(
        target, (xyxy[2], xyxy[3]), (xyxy[2], xyxy[3] - linelen),
        col, thickness
    )


class Vehicle:
    def __init__(self, vid, xyxy):
        self.vid = vid
        self.assign(xyxy)
        self.count = 0

    def assign(self, xyxy):
        self.xyxy = xyxy
        self.x1, self.y1, self.x2, self.y2 = list(map(int, xyxy))
        self.w = self.x2 - self.x1
        self.h = self.y2 - self.y1
        self.xc = int(self.x1 + self.w / 2)
        self.yc = int(self.y1 + self.h / 2)

        self.fade = 0
        try:
            self.tracked = True
        except AttributeError:
            self.tracked = False

        try:
            self.age += 1
        except AttributeError:
            self.age = 0


class Vehicles:
    def __init__(self):
        self.lst = []
        self.candidates = []
        self.vids = 0
        self.count = 0

    # process a box to see if position matches an existing object
    # if not create a new object
    def process(self, xyxy):
        x1, y1, x2, y2 = list(map(int, xyxy))
        w = x2 - x1
        h = y2 - y1
        xc = int(x1 + w / 2)
        yc = int(y1 + h / 2)

        if in_box(xc, yc, drw_box) and box.cls[0] in validcls:
            # check if object matches an existing tracked object
            for v in self.lst:
                if in_box(xc, yc, [v.x1, v.y1, v.x2, v.y2]):
                    v.assign(xyxy)
                    return

            # unique vehicle id
            vid = self.vids
            self.vids += 1

            # create new object
            self.lst.append(Vehicle(vid, xyxy))

    def draw(self):
        for v in self.lst:
            # currently tracked object
            if v.fade < 2 and v.age >= 3:
                # for tracked items:
                # red circle and green corners if object is not yet counted
                # green circle and green box otherwise
                if v.count == 0 and v.yc < cnt_box[1]:
                    cv2.circle(frame, (v.xc, v.yc), 2, cols['red'], 2)
                    draw_corners(
                        frame, (v.x1, v.y1, v.x2, v.y2), cols['green'], 1
                    )
                else:
                    if v.count > 0:
                        cv2.circle(frame, (v.xc, v.yc), 2, cols['green'], 2)
                        cv2.putText(
                            frame, str(v.count), (v.x1 - 10, v.y1 - 10),
                            font, 1, cols['green'], 1
                            )
                        cv2.rectangle(
                            frame, (v.x1, v.y1), (v.x2, v.y2), cols['green'], 1
                        )
                    else:
                        draw_corners(
                            frame, (v.x1, v.y1, v.x2, v.y2), cols['green'], 1
                        )

            # blue box if new object (tracked less than 3 times)
            # or red box if object is losing track
            elif (v.fade > 3 and v.count == 0):
                cv2.rectangle(
                    frame, (v.x1, v.y1), (v.x2, v.y2), cols['red'], 1
                )
            elif v.age < 3:
                cv2.rectangle(
                    frame, (v.x1, v.y1), (v.x2, v.y2), cols['blue'], 1
                )
        # count box rectangle
        cv2.rectangle(
            frame, (cnt_box[0], cnt_box[1]),
            (cnt_box[2], cnt_box[3]), cols['blue'], 1
        )

    def cnt(self):
        for v in self.lst:
            if not v.tracked:
                v.fade += 1
            v.tracked = False

            if v.fade > 5:
                self.lst.remove(v)
            if in_box(v.xc, v.yc, cnt_box) and v.count == 0 and v.age > 5:
                v.count = vehicles.count + 1
                vehicles.count = vehicles.count + 1

        print(f"Vehicle count: {vehicles.count}")


# credit to https://www.youtube.com/watch?v=MNn9qKG2UFI for the example video
# this is the 480p version
cap = cv2.VideoCapture('example.mp4')
fps = 30  # original video fps

# select model from 0 to 4:
# higher numbers are more accurate, but require more
# computing power and resources
models = ('yolov8n.pt', 'yolov8s.pt', 'yolov8m.pt', 'yolov8l.pt', 'yolov8x.pt')
model = YOLO(models[2])

# select classes to be processed and displayed:
# 1:bike 2:car 3:motorbike 5:bus 7:truck
validcls = [2, 3, 5, 7]

# box where counting takes place
cnt_box = [120, 240, 490, 260]
drw_box = [0, 0, 530, 480]
font = cv2.FONT_HERSHEY_DUPLEX

cols = {
    'red': (0, 0, 255),
    'blue': (255, 0, 0),
    'green': (0, 255, 0)
}

delay = 0

vehicles = Vehicles()  # class object to store vehicles

# main loop
while True:
    start = time.time()
    frame = cap.read()[1]

    results = model(frame)

    for result in results:
        boxes = result.boxes
        for box in boxes:
            vehicles.process(box.xyxy[0])

    vehicles.cnt()  # vehicles in box to count

    vehicles.draw()

    cv2.imshow("Image", frame)

    delay = match_speed(fps, time.time() - start)

    key = cv2.waitKey(delay)
    # press esc or q to quit
    if key in [27, 113]:
        break

cap.release()
cv2.destroyAllWindows()
