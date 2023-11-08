# 이산화탄소농도 - 서보모터
import serial
import time
from gpiozero import Servo
from time import sleep

servo = Servo(18)

ser = serial.Serial("/dev/serial0", baudrate=9600, timeout=1)

window_open = False


def read_CO2():
    ser.write(b"\xFF\x01\x86\x00\x00\x00\x00\x00\x79")
    time.sleep(0.1)
    response = ser.read(9)
    if len(response) == 9 and response[0] == 0xFF and response[1] == 0x86:
        co2_level = (response[2] << 8) + response[3]
        return co2_level
    else:
        return None


def main_CO2():
    try:
        global window_open
        while True:
            servo.value = None
            co2 = read_CO2()
            if co2 is not None:
                print("co2농도: ", co2)
                if co2 >= 2500 and window_open == False:
                    servo_open()
                    window_open = True
                elif co2 < 2500 and window_open == True:
                    servo_close()
                    window_open = False
            else:
                print("데이터를 읽는데 문제가 발생했습니다.")
            time.sleep(1)
    except KeyboardInterrupt:
        ser.close()
        print("프로그램을 종료합니다.")


def servo_open():
    for i in range(1, 4):
        servo.max()
        sleep(1)
    servo.value = None


def servo_close():
    for i in range(1, 4):
        servo.min()
        sleep(2)
    servo.value = None


if __name__ == "__main__":
    main_CO2()
