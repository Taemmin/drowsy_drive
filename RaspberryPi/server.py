import socket
import time
import psutil as PS
import socket
import board
import digitalio
import adafruit_ssd1306
from PIL import Image, ImageDraw, ImageFont
import threading as tr
import serial
from gpiozero import Servo
import RPi.GPIO as GPIO
from time import sleep

WIDTH = 128
HEIGHT = 64
FONTSIZE = 20

LOOPTIME = 1.0
# I2C 통신
i2c = board.I2C()
oled = adafruit_ssd1306.SSD1306_I2C(WIDTH, HEIGHT, i2c, addr=0x3C)
# Clear display.
oled.fill(0)
oled.show()
# Create blank image for drawing.
# Make sure to create image with mode '1' for 1-bit color.
image = Image.new("1", (oled.width, oled.height))
# Get drawing object to draw on image.
draw = ImageDraw.Draw(image)
# Draw a black filled box
draw.rectangle((0, 0, oled.width, oled.height), outline=0, fill=0)
padding = 0
top = padding
bottom = oled.height-40
x = 33
# font = ImageFont.load_default()
font1 = ImageFont.truetype('godoMaum.ttf', FONTSIZE)
font2 = ImageFont.truetype('godoMaum.ttf', FONTSIZE-6)

# 서버의 IP 주소 또는 호스트 이름
HOST = '192.168.0.235' 

# 서버에서 사용할 포트 번호 (클라이언트와 일치해야 함)
PORT = 12345

# 소켓 생성
#socket생성 후 listen상태 만들기
server_socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
server_socket.bind((HOST,PORT))
server_socket.listen(5)

# GPIO 모드 설정 
GPIO.setmode(GPIO.BCM)

# DC + sensor
# 모터 상태
STOP  = 0
FORWARD  = 1
BACKWORD = 2

# 모터 채널
CH1 = 0
CH2 = 1

# PIN 입출력 설정
OUTPUT = 1
INPUT = 0

# PIN 설정
HIGH = 1
LOW = 0

# 실제 핀 정의
#PWM PIN
ENA = 26  #37 pin
ENB = 0   #27 pin

#GPIO PIN
IN1 = 19  #37 pin
IN2 = 13  #35 pin
IN3 = 6   #31 pin
IN4 = 5   #29 pin

# 핀 설정 함수
def setPinConfig(EN, INA, INB):        
    GPIO.setup(EN, GPIO.OUT)
    GPIO.setup(INA, GPIO.OUT)
    GPIO.setup(INB, GPIO.OUT)
    # 100khz 로 PWM 동작 시킴 
    pwm = GPIO.PWM(EN, 100) 
    # 우선 PWM 멈춤.   
    pwm.start(0) 
    return pwm

# 모터 제어 함수
def setMotorContorl(pwm, INA, INB, speed, stat):

    #모터 속도 제어 PWM
    pwm.ChangeDutyCycle(speed)  
    
    if stat == FORWARD:
        GPIO.output(INA, HIGH)
        GPIO.output(INB, LOW)
        
    #뒤로
    elif stat == BACKWORD:
        GPIO.output(INA, LOW)
        GPIO.output(INB, HIGH)
        
    #정지
    elif stat == STOP:
        GPIO.output(INA, LOW)
        GPIO.output(INB, LOW)
        
# 모터 제어함수 간단하게 사용하기 위해 한번더 래핑(감쌈)
def setMotor(ch, speed, stat):
    if ch == CH1:
        #pwmA는 핀 설정 후 pwm 핸들을 리턴 받은 값이다.
        setMotorContorl(pwmA, IN1, IN2, speed, stat)
    else:
        #pwmB는 핀 설정 후 pwm 핸들을 리턴 받은 값이다.
        setMotorContorl(pwmB, IN3, IN4, speed, stat)
  
#모터 핀 설정
#핀 설정후 PWM 핸들 얻어옴 
pwmA = setPinConfig(ENA, IN1, IN2)
pwmB = setPinConfig(ENB, IN3, IN4)

# GPIO 핀 모드를 설정합니다.
# GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

# 초음파 센서 핀 번호를 설정합니다.
TRIG = 23  # 초음파 송신 핀
ECHO = 24  # 초음파 수신 핀

# 프로그램 시작 메시지를 출력합니다.
print("Distance measurement in progress")

# TRIG와 ECHO 핀을 출력 및 입력으로 설정합니다.
GPIO.setup(TRIG, GPIO.OUT)
GPIO.setup(ECHO, GPIO.IN)

# 초음파 센서가 안정화되기를 기다립니다.
print("Waiting for sensor to settle")
GPIO.output(TRIG, False)
time.sleep(1)

def dcmotor1():
    setMotor(CH1, 70, FORWARD)
    setMotor(CH2, 70, FORWARD)
    
def dcmotor2():
    setMotor(CH1, 50, FORWARD)
    setMotor(CH2, 50, FORWARD)
    
def dcmotor3():
    setMotor(CH1, 100, STOP)
    setMotor(CH2, 100, STOP)

def dc_sensor():
    # 초음파 센서에 초음파 신호를 보냅니다.
    GPIO.output(TRIG, True)
    time.sleep(0.00001)
    GPIO.output(TRIG, False)

    # 초음파 신호를 수신할 때까지 대기합니다.
    while GPIO.input(ECHO) == 0:
        start = time.time()
    while GPIO.input(ECHO) == 1:
        stop = time.time()

    # 초음파 신호가 돌아오는 데 걸린 시간을 계산합니다.
    check_time = stop - start

    # 거리를 계산합니다. 초음파의 속도는 34300 cm/s입니다.
    distance = check_time * 34300 / 2

    # 측정된 거리를 출력합니다.
    print("Distance : %.1f cm" % distance)

    # 0.4초 동안 대기한 후 다음 측정을 수행합니다.
    time.sleep(0.4)
    
    if distance >= 15 and distance <= 20:
        dcmotor1()
    elif distance >= 10 and distance < 15:
        dcmotor2()
    elif distance < 10:
        dcmotor3()
    else:
        setMotor(CH1, 100, FORWARD)
        setMotor(CH2, 100, FORWARD)

# OLED
global oled_state
oled_state = False

def OLED_ON():
    draw.text((x, top), "warning!!!", font=font1, fill=255)
    draw.text((x, bottom), "차량 운전자 \n졸음운전 중!!!", font=font2, fill=255)
    # Display image
    oled.image(image)
    oled.show()
    global oled_state
    if oled_state == False:
        print("thread 생성")
        p1 = tr.Thread(target=OLED_OFF)
        p1.start()
    
def OLED_OFF():
    global oled_state
    oled_state = True
    print("oled off시작")
    time.sleep(5)
    oled.fill(0)
    oled.show()
    oled_state = False
    print("oled off 끝")

# #LED, 진동모터
motor_pin = 12
LED_pin = 25

GPIO.setup(motor_pin, GPIO.OUT)
GPIO.setup(LED_pin, GPIO.OUT)
GPIO.output(LED_pin, 0)

def vibe():
    for i in range(1, 11, 1):
        GPIO.output(motor_pin, GPIO.HIGH)
        GPIO.output(LED_pin, 1)
        time.sleep(0.3)
        GPIO.output(motor_pin, GPIO.LOW)
        GPIO.output(LED_pin, 0)
        time.sleep(0.3)

# CO2 측정 및 창문 개폐
servo = Servo(18)
ser = serial.Serial('/dev/serial0', baudrate=9600, timeout=1)

socket Android_socket = None

global window_open
window_open = False

def read_CO2():
    ser.write(b'\xFF\x01\x86\x00\x00\x00\x00\x00\x79')
    time.sleep(0.1)
    response = ser.read(9)
    if len(response) == 9 and response[0] == 0xFF and response[1] == 0x86:
        co2_level = (response[2] << 8) + response[3]
        return co2_level
    else:
        return None

# 창문 열림
def servo_open():
    servo.max() 
    time.sleep(1.7)
    servo.value = None

# 창문 닫힘
def servo_close():
    servo.min()
    time.sleep(2.15)
    servo.value = None

# CO2 측정 후 창문개폐
def co2():
    global window_open
    global co2_str
    while True:
        servo.value = None
        co2 = read_CO2()
        if co2 is not None:
            print("co2농도: ", co2)
            if co2 >= 2000 and window_open == False:
                servo_open()
                window_open = True
                client_socket.send("2\n".encode("utf-8"))  # 창문개폐횟수 데이터를 클라이언트에게 전송
                print("창문개폐횟수 보냄")
            elif co2 < 2000 and window_open == True:
                servo_close()
                window_open = False
        else:
            print('데이터를 읽는데 문제가 발생했습니다.')
        time.sleep(1)

#thread를 생성하는 threaded함수 구현
def threaded(client_socket):
    
    global Android_socket
    
    print('thread Connected')
    while True:
        try:
            co2 = read_CO2()
            data = client_socket.recv(1024) #client가 보낸 메세지를 받아 data에 저장
            print('Received from : [', data.decode(), ']') #받은 데이터 출력
            if data.decode('utf-8') == 'sleep':
                print("sleep receive")
                if Android_socket is not None:
                    print("안드로이드에 sleep 보냄")
                    Android_socket.send("1\n".encode("utf-8"))  # 졸음횟수 데이터를 클라이언트에게 전송
                print("졸음횟수 보냄")
                OLED_ON()
                dc_sensor()
                vibe()
            
            if data.decode('utf-8') == 'front':
                if Android_socket is not None:
                    print("안드로이드에 front 보냄")
                    Android_socket.send("3\n".encode("utf-8"))  # 전방미주시횟수 데이터를 클라이언트에게 전송
                print("전방미주시횟수 보냄")
            
            if data.decode('utf-8') not in 'AndroidMessage':
                print("안드로이드 소켓 저장")
                co2_str = str(co2) + "\n"  # CO2 값을 문자열로 변환
                co2_data = co2_str.encode("utf-8")  # 문자열을 바이트로 인코딩
                Android_socket = client_socket
                client_socket.send(co2_data)  # CO2 데이터를 클라이언트에게 전송
                print("co2값 보냄")
                
            if not data:
                print('Disconnected by ')
                break

            #client에 받은 데이터 재전송
            client_socket.send(data)

        #conncetcionError의 서브클래스로, 연결 시도가 상대방에 의해 중단될 때 발생.
        except ConnectionResetError as e:
            print('Disconnected by ')
            break

    #client와 연결 끊음    
    client_socket.close()


setMotor(CH1, 100, FORWARD)
setMotor(CH2, 100, FORWARD)

p2 = tr.Thread(target=co2)
p2.start()
print("thread2 생성")


# 메시지 대기
while True:
    print('wait')
    client_socket,addr = server_socket.accept()
    print("연결됨")
    thread1 = tr.Thread(target=threaded, args = (client_socket,))
    thread1.start()
    print("thread 생성")