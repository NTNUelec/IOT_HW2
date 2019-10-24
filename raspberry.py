import sys
import time
import argparse
import threading

import serial


parser = argparse.ArgumentParser()
parser.add_argument("-s", "--serial", required=True, help="serial device path")
parser.add_argument("-b", "--baudrate", required=True, help="baudrate of serial device")
parser.add_argument("-d", "--debug", help="debug mode")

class RxThread(threading.Thread):

    def __init__(self, sys_state, ser):
        super(RxThread, self).__init__()
        self.sys_state = sys_state
        self.ser = ser
        self.stop = False

    def run(self):
        """Recieve lightup boolean, and compute the ideal pwm value for Uno"""
        while not self.stop:
            # If there is content in serial input buffer, read it
            if self.ser.inWaiting():
                # Update ideal_pwm
                current_rps = int(self.ser.readline().decode('utf8')[:-2])
                reference_rps = self.sys_state['reference_rps']
                
                # PI Controller
                # ============
                if current_rps < reference_rps:
                    # Upper bound of ideal_pwm is 130 (tested)
                    self.sys_state['ideal_pwm'] += 0.2*abs(current_rps - reference_rps)
                    self.sys_state['ideal_pwm'] += 0.1*self.sys_state['past_error_sum']
                    self.sys_state['ideal_pwm'] = min(self.sys_state['ideal_pwm'], 130)       
                    
                if current_rps > reference_rps:
                    # Lower bound of ideal_pwm is 0 (tested)
                    self.sys_state['ideal_pwm'] -= 0.2*abs(current_rps - reference_rps)
                    self.sys_state['ideal_pwm'] -= 0.1*self.sys_state['past_error_sum']
                    self.sys_state['ideal_pwm'] = max(self.sys_state['ideal_pwm'], 0)
                    
                self.sys_state['past_error_sum'] = 0.5*self.sys_state['past_error_sum'] + 0.5*abs(current_rps - reference_rps)                
                print("Reference: %3d, Current: %4d" % (reference_rps, current_rps), end="\r")


class TxThread(threading.Thread):

    def __init__(self, sys_state, ser):
        super(TxThread, self).__init__()
        self.sys_state = sys_state
        self.ser = ser
        self.stop = False

    def run(self):
        """Send pull request and ideal pwm to Uno if needed"""
        while not self.stop:
            # Send ideal pwm to Uno
            content = 'r' + str(self.sys_state['ideal_pwm'])
            self.ser.write(content.encode())

            # Send pull request to Uno
            self.ser.write("p".encode())

            # Sleep for a period of time
            time.sleep(self.sys_state['interval_time'])


def main(args):
    # System State Initialization
    sys_state = {        
        'past_error_sum': 0,
        'reference_rps': 0,
        'ideal_pwm': 0,
        'interval_time': 0.001
    }

    # Open Tx/Rx communication channel
    ser = serial.Serial(str(args.serial), int(args.baudrate), timeout=0.5)

    # Run Tx/Rx threads to communiate with Uno
    rx = RxThread(sys_state, ser)
    tx = TxThread(sys_state, ser)
    rx.start()
    tx.start()

    # Interact with user
    while True:
        command = input()

        if command == 'q':
            # Gracefully clean up
            rx.stop = True
            tx.stop = True
            ser.close()
            break
        else:
            # Update reference rps
            reference_rps = int(command)
            sys_state['reference_rps'] = reference_rps

if __name__ == "__main__":
    args = parser.parse_args()
    main(args)
