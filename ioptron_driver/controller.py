#!/usr/bin/env python3
"""
| iOptron Driver for Linux
| Matheus J. Castro

| This is the main file. Here you find the main classes.
"""

import serial
import time


class MountConnectionError(Exception):
    pass


class WrongCommand(Exception):
    pass


class IoptronDevices:
    devices_ref = {
        "0010": "Cube_II_Cube_Pro_EQ_mode", 
        "0011": "SmartEQ_Pro_Plus", 
        "0025": "CEM25_CEM25P", 
        "0026": "CEM25-EC", 
        "0030": "iEQ30_Pro", 
        "0040": "CEM40", 
        "0041": "CEM40-EC", 
        "0045": "iEQ45_Pro_EQ_mode", 
        "0046": "iEQ45_Pro_AA_mode", 
        "0060": "CEM60",
        "0061": "CEM60-EC", 
        "5010": "Cube_II_Cube_Pro_AA_mode", 
        "5035": "AZ_Mount_Pro"
    }


class IoptronCommands:

    # PositionStatus
    longitude_latitude_status = "GLS"      # longitude, latitude & status
    local_time_info = "GLT"                # local time/time zone info
    declination_right_ascension = "GEC"    # current declination & right ascension
    altitude_azimuth = "GAC"               # altitude & azimuth
    parking_position = "GPC"               # parking position alt/az
    max_slew_rate = "GSR"                  # maximum slewing speed
    altitude_limit = "GAL"                 # altitude limit (tracking & slewing)
    guiding_rate = "AG"                    # guiding rate (RA & DEC)
    meridian_treatment = "GMT"             # meridian treatment mode/limit

    # Change Settings
    
    # Tracking rate
    @staticmethod
    def tracking_rate(rate: int) -> str:
        if type(rate) is not int or rate not in range(0, 5):
            raise WrongCommand("'tracking_rate' must be an int between 0 and 4.")
        return f"RT{rate}"

    # Moving rate
    @staticmethod
    def  moving_rate(rate: int) -> str:
        if type(rate) is not int or rate not in range(1, 10):
            raise WrongCommand("'moving_rate' must be an int between 1 and 9.")
        return f"SR{rate}"

    # UTC offset in minutes
    @staticmethod
    def utc_offset(minutes: int) -> str:
        if type(minutes) is not int or not (-720 <= minutes <= 780):
            raise WrongCommand("'utc_offset' must be an int between -720 and +780 minutes.")
        sign = "+" if minutes >= 0 else "-"
        return f"SG{sign}{abs(minutes):03d}"

    # Daylight Saving Time
    @staticmethod
    def daylight_saving(enabled: int) -> str:
        if enabled not in (0, 1):
            raise WrongCommand("'daylight_saving' must be 0 or 1.")
        return f"SDS{enabled}"

    # Set local date
    @staticmethod
    def set_date(year: int, month: int, day: int) -> str:
        if not (0 <= year <= 99):
            raise WrongCommand("Year must be an int between 00 and 99.")
        if not (1 <= month <= 12):
            raise WrongCommand("Month must be an int between 1 and 12.")
        if not (1 <= day <= 31):
            raise WrongCommand("Day must be an int between 1 and 31.")
        return f"SC{year:02d}{month:02d}{day:02d}"

    # Set local time
    @staticmethod
    def set_time(hour: int, minute: int, second: int) -> str:
        if not (0 <= hour <= 23):
            raise WrongCommand("Hour must be an int between 0 and 23.")
        if not (0 <= minute <= 59):
            raise WrongCommand("Minute must be an int between 0 and 59.")
        if not (0 <= second <= 59):
            raise WrongCommand("Second must be an int between 0 and 59.")
        return f"SL{hour:02d}{minute:02d}{second:02d}"

    # Longitude (arc-seconds)
    @staticmethod
    def longitude(value: int) -> str:
        if type(value) is not int or not (-648000 <= value <= 648000):
            raise WrongCommand("'longitude' must be an int between -648000 and +648000 arcsec.")
        sign = "+" if value >= 0 else "-"
        return f"Sg{sign}{abs(value):06d}"

    # Latitude (arc-seconds)
    @staticmethod
    def latitude(value: int) -> str:
        if type(value) is not int or not (-324000 <= value <= 324000):
            raise WrongCommand("'latitude' must be an int between -324000 and +324000 arcsec.")
        sign = "+" if value >= 0 else "-"
        return f"St{sign}{abs(value):06d}"

    # Hemisphere
    @staticmethod
    def hemisphere(value: int) -> str:
        if value not in (0, 1):
            raise WrongCommand("'hemisphere' must be 0 (South) or 1 (North).")
        return f"SHE{value}"

    # Maximum slewing speed
    @staticmethod
    def set_max_slew_rate(rate: int) -> str:
        if rate not in (7, 8, 9):
            raise WrongCommand("'max_slew_rate' must be 7, 8, or 9.")
        return f"MSR{rate}"

    # Altitude limit
    @staticmethod
    def set_altitude_limit(value: int) -> str:
        if type(value) is not int or not (-89 <= value <= 89):
            raise WrongCommand("'altitude_limit' must be between -89 and +89 degrees.")
        sign = "+" if value >= 0 else "-"
        return f"SAL{sign}{abs(value):02d}"

    # Guiding rate
    @staticmethod
    def set_guiding_rate(ra: int, dec: int) -> str:
        if not (1 <= ra <= 90):
            raise WrongCommand("RA guiding rate must be between 01 and 90 (0.01-0.90).")
        if not (10 <= dec <= 99):
            raise WrongCommand("DEC guiding rate must be between 10 and 99 (0.10-0.99).")
        return f"RG{ra:02d}{dec:02d}"

    # Meridian treatment
    @staticmethod
    def set_meridian_treatment(mode: int, degrees: int) -> str:
        if mode not in (0, 1):
            raise WrongCommand("Mode must be 0 (stop) or 1 (flip).")
        if not (0 <= degrees <= 99):
            raise WrongCommand("Degrees past meridian must be between 0 and 99.")
        return f"SMT{mode}{degrees:02d}"

    # Mount Motion
    
    slew = "MS"             # Slew to the most recently defined coordinates
    stop_slew = "Q"         # Stop slewing only
    park = "MP1"            # Park mount to the most recently defined parking position
    unpark = "MP0"          # Unpark mount
    go_home = "MH"          # Slew immediately to zero/home position
    search_home = "MSH"     # Automatically search the mechanical home position using sensors
    stop_motion = "q"       # Stop movement from arrow commands (:mn, :me, :ms, :mw)
    stop_lr = "qR"          # Stop left/right movement
    stop_ud = "qD"          # Stop up/down movement

    # Continuous motion (like pressing arrow keys)
    move_north = "mn"
    move_east = "me"
    move_south = "ms"
    move_west = "mw"

    # Set tracking state
    @staticmethod
    def tracking(enabled: int) -> str:
        if enabled not in (0, 1):
            raise WrongCommand("'tracking' must be 0 (stop) or 1 (start).")
        return f"ST{enabled}"

    # Guide north for specified milliseconds
    @staticmethod
    def guide_north(ms: int) -> str:
        print(ms)
        if type(ms) is not int or not (0 <= ms <= 99999):
            raise WrongCommand("'guide_north' must be between 0 and 99999 ms.")
        return f"Mn{ms:05d}"

    # Guide east for specified milliseconds
    @staticmethod
    def guide_east(ms: int) -> str:
        if type(ms) is not int or not (0 <= ms <= 99999):
            raise WrongCommand("'guide_east' must be between 0 and 99999 ms.")
        return f"Me{ms:05d}"

    # Guide south for specified milliseconds
    @staticmethod
    def guide_south(ms: int) -> str:
        if type(ms) is not int or not (0 <= ms <= 99999):
            raise WrongCommand("'guide_south' must be between 0 and 99999 ms.")
        return f"Ms{ms:05d}"

    # Guide west for specified milliseconds
    @staticmethod
    def guide_west(ms: int) -> str:
        if type(ms) is not int or not (0 <= ms <= 99999):
            raise WrongCommand("'guide_west' must be between 0 and 99999 ms.")
        return f"Mw{ms:05d}"

    # Custom RA tracking rate (n.nnnn * sidereal rate)
    @staticmethod
    def custom_ra_rate(rate: float) -> str:
        if not (0.5 <= rate <= 1.5):
            raise WrongCommand("'custom_ra_rate' must be between 0.5000 and 1.5000.")
        value = int(rate * 10000)
        return f"RR{value:05d}"
    
    # Position

    # Commands without input
    calibrate_mount = "CM"          # Synchronize / calibrate mount
    set_zero = "SZP"       # Set current position as zero position

    # Set commanded Right Ascension
    @staticmethod
    def set_ra(value: str) -> str:
        if type(value) is not str or len(value) != 8:
            raise WrongCommand("'set_ra' requires an 8 character string.")
        return f"Sr{value}"

    # Set commanded Declination
    @staticmethod
    def set_dec(value: str) -> str:
        if type(value) is not str or len(value) != 8:
            raise WrongCommand("'set_dec' requires an 8 character string.")
        return f"Sds{value}"

    # Set commanded Altitude
    @staticmethod
    def set_altitude(value: str) -> str:
        if type(value) is not str or len(value) != 8:
            raise WrongCommand("'set_altitude' requires an 8 character string.")
        return f"Sas{value}"

    # Set commanded Azimuth
    @staticmethod
    def set_azimuth(value: str) -> str:
        if type(value) is not str or len(value) != 9:
            raise WrongCommand("'set_azimuth' requires a 9 character string.")
        return f"Sz{value}"

    # Set parking azimuth
    @staticmethod
    def set_parking_azimuth(value: str) -> str:
        if type(value) is not str or len(value) != 9:
            raise WrongCommand("'set_parking_azimuth' requires a 9 character string.")
        return f"SPA{value}"

    # Set parking altitude
    @staticmethod
    def set_parking_altitude(value: str) -> str:
        if type(value) is not str or len(value) != 8:
            raise WrongCommand("'set_parking_altitude' requires an 8 character string.")
        return f"SPH{value}"

    # Misc
    firmware_main_and_hc_date = "FW1"      # firmware date: mainboard & hand controller
    firmware_motor_date = "FW2"            # firmware date: RA & Dec motor boards
    mount_model = "MountInfo"              # gets the mount model


class IoptronCall:
    def __init__(self, main_instance, commands, fast=False):
        if fast:
            self.send = main_instance.fast_send_cmd
        else:
            self.send = main_instance.send_cmd

        self.commands = commands

    def __getattr__(self, name):
        def call(*args):
            return self.send(cmd(*args))

        cmd = getattr(self.commands, name)
        if callable(cmd):
            return lambda *values: call(*values)
        else:
            return self.send(cmd)


class Ioptron(IoptronDevices, IoptronCommands):
    def __init__(self, port):
        self.port = port
        self.baudrate = 115200
        self.bytesize = 8
        self.parity = "N"
        self.stopbits = 1
        self.serial_timeout = 2

        self.device = None

        self.device_num = None
        self.device_name = None

        self.exec = IoptronCall(self, IoptronCommands, fast=True)
        self.exec.read = IoptronCall(self, IoptronCommands)


    def init_serial(self, timedate=True):
        self.device = serial.Serial(
            port=self.port,
            baudrate=self.baudrate,
            bytesize=self.bytesize,
            parity=self.parity,
            stopbits=self.stopbits,
            timeout=self.serial_timeout,
        )

        self.device_num = self.send_cmd(self.mount_model)

        if self.device_num is None or self.device_num == "":
            raise MountConnectionError("Device did not respond.")
        else:
            self.device_name = self.devices_ref.get(self.device_num, "Unknown device.")

            if timedate:
                self.set_current_timedate()

            return 1

        

    def health_check(self):
        if self.device_num != self.send_cmd(self.mount_model):
            raise MountConnectionError("Health check failed.")
        else:
            return 1

    def close_serial(self):
        self.device.close()
        return 1

    def send_cmd(self, data):
        data = self.format_command(data)
        self.device.write(data.encode())
        time.sleep(0.01)
        line = self.device.read_until(b"#")
        return line.decode().strip("#")

    def fast_send_cmd(self, data):
        data = self.format_command(data)
        self.device.write(data.encode())
        return 1

    @staticmethod
    def format_command(data):
        if type(data) is not str:
            raise TypeError("Command should be a string.")
        elif " " in data:
            raise ValueError("Command should not have spaces.")
        return ":" + data + "#"

    def set_current_timedate(self):
        curr_time = time.localtime()

        # UTC offset em min
        if curr_time.tm_isdst and time.daylight:
            utc_offset_minutes = -time.altzone // 60
        else:
            utc_offset_minutes = -time.timezone // 60

        status = []
        status.append(self.exec.read.set_date(curr_time.tm_year-2000, curr_time.tm_mon, curr_time.tm_mday) == "1")
        status.append(self.exec.read.set_time(curr_time.tm_hour, curr_time.tm_min, curr_time.tm_sec) == "1")
        status.append(self.exec.read.utc_offset(utc_offset_minutes) == "1")
        status.append(self.exec.read.daylight_saving(0) == "1")

        if not all(status):
            raise MountConnectionError("Error while setting the current time and date.")