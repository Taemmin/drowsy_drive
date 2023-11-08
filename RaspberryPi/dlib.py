import cv2
import dlib
from functools import wraps
from scipy.spatial import distance
import time
import os
import socket # 소켓통신을 위한 라이브러리

Host = '192.168.0.235'
Port = 12345

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((Host,Port))

# 카메라 셋팅
cap = cv2.VideoCapture(0)
cap.set(3, 320)
cap.set(4, 240)
# dlib 인식 모델 정의
hog_face_detector = dlib.get_frontal_face_detector()
dlib_facelandmark = dlib.shape_predictor("shape_predictor_68_face_landmarks.dat")
# GPIO 셋팅
last_face_detection_time = time.time()  # 마지막 얼굴 감지 시간 초기화
last_closed_eyes_detection_time = None #마지막 눈 감음 감지 시간 초기화

def calculate_EAR(eye):
    A = distance.euclidean(eye[1], eye[5])
    B = distance.euclidean(eye[2], eye[4])
    C = distance.euclidean(eye[0], eye[3])
    ear_aspect_ratio = (A + B) / (2.0 * C)
    return ear_aspect_ratio



def close():
    cv2.putText(frame, "Closed", (20, 100), cv2.FONT_HERSHEY_SIMPLEX, 3, (0, 0, 255), 4)



# 주요 루프 시작
while True:
    

    _, frame = cap.read()
    if frame is None:
        print("프레임 읽을 수 없음")
        break
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    
    
    # 얼굴 검출
    faces = hog_face_detector(gray)
    if len(faces) > 0:
        last_face_detection_time = time.time()  # 마지막 얼굴 감지 시간 업데이트
    
    
    # 2초 동안 얼굴이 검출되지 않으면 "전방미주시" 메시지를 표시
    if time.time() - last_face_detection_time > 2.0:
        cv2.putText(frame, "front", (20, 100), cv2.FONT_HERSHEY_SIMPLEX, 3, (0, 0, 255), 4)
        
        send_front = "front"
        encode_send_front = send_front.encode('utf-8')
        s.send(encode_send_front)
    
    
    for face in faces:
        face_landmarks = dlib_facelandmark(gray, face)
        leftEye = []
        rightEye = []
        for n in range(36, 42):
            x = face_landmarks.part(n).x
            y = face_landmarks.part(n).y
            leftEye.append((x, y))
        for n in range(42, 48):
            x = face_landmarks.part(n).x
            y = face_landmarks.part(n).y
            rightEye.append((x, y))
        
        left_ear = calculate_EAR(leftEye)
        right_ear = calculate_EAR(rightEye)
        EAR = (left_ear + right_ear) / 2
        EAR = round(EAR, 2)
        
        if EAR < 0.18:
            close()
            
            if last_closed_eyes_detection_time == None:
                last_closed_eyes_detection_time = time.time()

            if last_closed_eyes_detection_time is not None and time.time() - last_closed_eyes_detection_time >= 1.0:
                print("real sleep")
                send_sleep = "sleep"
                encode_send_sleep = send_sleep.encode('utf-8')
                s.send(encode_send_sleep)
                last_closed_eyes_detection_time = None
        else:
            last_closed_eyes_detection_time = None

        print(EAR)
    cv2.imshow("Are you Sleepy?", frame)
    key = cv2.waitKey(30)
    if key == 27:
        break
    time.sleep(0.1)



cap.release()
cv2.destroyAllWindows()