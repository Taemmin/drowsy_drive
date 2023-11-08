# RPi.GPIO 모듈을 GPIO로 import합니다.
import RPi.GPIO as GPIO
import time
from time import sleep

# 모터 상태
STOP = 0
FORWARD = 1
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
# PWM PIN
ENA = 26  # 37 pin
ENB = 0  # 27 pin

# GPIO PIN
IN1 = 19  # 37 pin
IN2 = 13  # 35 pin
IN3 = 6  # 31 pin
IN4 = 5  # 29 pin


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
    # 모터 속도 제어 PWM
    pwm.ChangeDutyCycle(speed)

    if stat == FORWARD:
        GPIO.output(INA, HIGH)
        GPIO.output(INB, LOW)

    # 뒤로
    elif stat == BACKWORD:
        GPIO.output(INA, LOW)
        GPIO.output(INB, HIGH)

    # 정지
    elif stat == STOP:
        GPIO.output(INA, LOW)
        GPIO.output(INB, LOW)


# 모터 제어함수 간단하게 사용하기 위해 한번더 래핑(감쌈)
def setMotor(ch, speed, stat):
    if ch == CH1:
        # pwmA는 핀 설정 후 pwm 핸들을 리턴 받은 값이다.
        setMotorContorl(pwmA, IN1, IN2, speed, stat)
    else:
        # pwmB는 핀 설정 후 pwm 핸들을 리턴 받은 값이다.
        setMotorContorl(pwmB, IN3, IN4, speed, stat)


# GPIO 모드 설정
GPIO.setmode(GPIO.BCM)

# 모터 핀 설정
# 핀 설정후 PWM 핸들 얻어옴
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
time.sleep(2)


def dcmotor1():
    setMotor(CH1, 70, FORWARD)
    setMotor(CH2, 70, FORWARD)


def dcmotor2():
    setMotor(CH1, 50, FORWARD)
    setMotor(CH2, 50, FORWARD)


def dcmotor3():
    setMotor(CH1, 100, STOP)
    setMotor(CH2, 100, STOP)


try:
    while True:
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

        setMotor(CH1, 80, FORWARD)
        setMotor(CH2, 80, FORWARD)

        if distance >= 15 and distance <= 20:
            dcmotor1()
        elif distance >= 10 and distance < 15:
            dcmotor2()
        elif distance < 10:
            dcmotor3()
        else:
            setMotor(CH1, 100, FORWARD)
            setMotor(CH2, 100, FORWARD)

except KeyboardInterrupt:
    # 사용자가 Ctrl+C로 프로그램을 중지할 때 정리 작업을 수행합니다.
    print("measurement stopped by User")
    GPIO.cleanup()
