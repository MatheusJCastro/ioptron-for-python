#!/usr/bin/env python3
"""
| iOptron Driver for Linux
| Matheus J. Castro

| This is the main file. aaaHere you find the main classes.
"""

import serial
import time


class MountConnectionError(Exception):
    """
    Class to raise Mount Connection Errors
    """

    pass


class WrongCommand(Exception):
    """
    Class to raise Wrong Commands Errors
    """

    pass


class IoptronDevices:
    """
    Define all RS-232-enabled iOptron devices and their code-tags.
    """

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
    """
    | Define all iOptron RS-232 Command Language commands.
    | - iOptron Mount RS-232 Command Language 2014, Version 2.5 from Jan. 15th 2019.
    """

    # PositionStatus
    longitude_latitude_status = "GLS"      
    """Get longitude, latitude & status."""
    local_time_info = "GLT"                
    """Get local time/time zone info."""
    declination_right_ascension = "GEC"    
    """Get current declination & right ascension."""
    altitude_azimuth = "GAC"
    """Get altitude & azimuth."""
    parking_position = "GPC"               
    """Get parking position alt/az."""
    max_slew_rate = "GSR"                  
    """Get maximum slewing speed."""
    altitude_limit = "GAL"                 
    """Get altitude limit (tracking & slewing)."""
    guiding_rate = "AG"                    
    """Get guiding rate (RA & DEC)."""
    meridian_treatment = "GMT"             
    """Get meridian treatment mode/limit."""

    # Change Settings
    @staticmethod
    def tracking_rate(rate: int) -> str:
        """
        Set the tracking rate.

        :param rate: an int (n) between 0 and 4.
        :return: RTn.
        """

        if type(rate) is not int or rate not in range(0, 5):
            raise WrongCommand("'tracking_rate' must be an int between 0 and 4.")
        return f"RT{rate}"

    @staticmethod
    def  moving_rate(rate: int) -> str:
        """
        Set the moving rate.

        :param rate: an int (n) between 1 and 9.
        :return: SRn.
        """

        if type(rate) is not int or rate not in range(1, 10):
            raise WrongCommand("'moving_rate' must be an int between 1 and 9.")
        return f"SR{rate}"

    @staticmethod
    def utc_offset(minutes: int) -> str:
        """
        Set the UTC offset in minutes.

        :param minutes: an int (sMMM) between -720 and 780.
        :return: SGsMMM.
        """

        if type(minutes) is not int or not (-720 <= minutes <= 780):
            raise WrongCommand("'utc_offset' must be an int between -720 and +780 minutes.")
        sign = "+" if minutes >= 0 else "-"
        return f"SG{sign}{abs(minutes):03d}"

    @staticmethod
    def daylight_saving(enabled: int) -> str:
        """
        Enable or disable the Daylight Saving Time.

        :param enabled: 0 or 1 (n).
        :return: SDSn.
        """
        
        if enabled not in (0, 1):
            raise WrongCommand("'daylight_saving' must be 0 or 1.")
        return f"SDS{enabled}"

    @staticmethod
    def set_date(year: int, month: int, day: int) -> str:
        """
        Set local date.

        :param year: an int between 0 and 99 (YY).
        :param month: an int between 1 and 12 (MM).
        :param day: an int between 1 and 31 (DD).
        :return: SCYYMMDD.
        """

        if not (0 <= year <= 99):
            raise WrongCommand("Year must be an int between 0 and 99.")
        if not (1 <= month <= 12):
            raise WrongCommand("Month must be an int between 1 and 12.")
        if not (1 <= day <= 31):
            raise WrongCommand("Day must be an int between 1 and 31.")
        return f"SC{year:02d}{month:02d}{day:02d}"

    @staticmethod
    def set_time(hour: int, minute: int, second: int) -> str:
        """
        Set local time.

        :param hour: an int between 0 and 23 (HH).
        :param minute: an int between 0 and 59 (MM).
        :param second: an int between 0 and 59 (SS).
        :return: SLHHMMSS.
        """

        if not (0 <= hour <= 23):
            raise WrongCommand("Hour must be an int between 0 and 23.")
        if not (0 <= minute <= 59):
            raise WrongCommand("Minute must be an int between 0 and 59.")
        if not (0 <= second <= 59):
            raise WrongCommand("Second must be an int between 0 and 59.")
        return f"SL{hour:02d}{minute:02d}{second:02d}"

    @staticmethod
    def longitude(value: int) -> str:
        """
        Set the Longitude (arc-seconds).

        :param value: an int (sSSSSSS) between -648000 and 648000.
        :return: SgsSSSSSS.
        """

        if type(value) is not int or not (-648000 <= value <= 648000):
            raise WrongCommand("'longitude' must be an int between -648000 and +648000 arcsec.")
        sign = "+" if value >= 0 else "-"
        return f"Sg{sign}{abs(value):06d}"

    @staticmethod
    def latitude(value: int) -> str:
        """
        Set the Latitude (arc-seconds).

        :param value: an int (sSSSSSS) between -324000 and 324000.
        :return: StsSSSSSS.
        """

        if type(value) is not int or not (-324000 <= value <= 324000):
            raise WrongCommand("'latitude' must be an int between -324000 and +324000 arcsec.")
        sign = "+" if value >= 0 else "-"
        return f"St{sign}{abs(value):06d}"

    @staticmethod
    def hemisphere(value: int) -> str:
        """
        Set the Hemisphere.

        :param value: 0 for south or 1 for north (n).
        :return: SHEn.
        """

        if value not in (0, 1):
            raise WrongCommand("'hemisphere' must be 0 (South) or 1 (North).")
        return f"SHE{value}"

    @staticmethod
    def set_max_slew_rate(rate: int) -> str:
        """
        Set the Maximum slewing speed.

        :param rate: 7, 8 or 9 (n).
        :return: MSRn.
        """

        if rate not in (7, 8, 9):
            raise WrongCommand("'max_slew_rate' must be 7, 8, or 9.")
        return f"MSR{rate}"

    @staticmethod
    def set_altitude_limit(value: int) -> str:
        """
        Set the Altitude limit.

        :param value: an int (snn) between -89 and 89.
        :return: SALsnn.
        """

        if type(value) is not int or not (-89 <= value <= 89):
            raise WrongCommand("'altitude_limit' must be between -89 and +89 degrees.")
        sign = "+" if value >= 0 else "-"
        return f"SAL{sign}{abs(value):02d}"

    @staticmethod
    def set_guiding_rate(ra: int, dec: int) -> str:
        """
        Set the Guiding rate.

        :param ra: an int (nn) between 1 and 90 (0.01-0.90).
        :param def: an int (nn) between 10 and 99 (0.10-0.99).
        :return: RGnnnn.
        """

        if not (1 <= ra <= 90):
            raise WrongCommand("RA guiding rate must be between 1 and 90 (0.01-0.90).")
        if not (10 <= dec <= 99):
            raise WrongCommand("DEC guiding rate must be between 10 and 99 (0.10-0.99).")
        return f"RG{ra:02d}{dec:02d}"

    @staticmethod
    def set_meridian_treatment(mode: int, degrees: int) -> str:
        """
        Set the Meridian treatment.

        :param mode: 0 to stop or 1 to flip (n).
        :param degrees: an int (nn) between 0 and 99.
        :return: SMTnnn.
        """

        if mode not in (0, 1):
            raise WrongCommand("Mode must be 0 (stop) or 1 (flip).")
        if not (0 <= degrees <= 99):
            raise WrongCommand("Degrees past meridian must be between 0 and 99.")
        return f"SMT{mode}{degrees:02d}"

    # Mount Motion
    slew = "MS"             
    """Slew to the most recently defined coordinates."""
    stop_slew = "Q"         
    """Stop slewing only."""
    park = "MP1"            
    """Park mount to the most recently defined parking position."""
    unpark = "MP0"          
    """Unpark mount."""
    go_home = "MH"          
    """Slew immediately to zero/home position."""
    search_home = "MSH"     
    """Automatically search the mechanical home position using sensors."""
    stop_motion = "q"       
    """Stop movement from arrow commands (:mn, :me, :ms, :mw)."""
    stop_lr = "qR"          
    """Stop left/right movement."""
    stop_ud = "qD"          
    """Stop up/down movement."""

    move_north = "mn"
    """Continuous motion (like pressing arrow keys) to north until stop_motion is called."""
    move_east = "me"
    """Continuous motion (like pressing arrow keys) to east until stop_motion is called."""
    move_south = "ms"
    """Continuous motion (like pressing arrow keys) to south until stop_motion is called."""
    move_west = "mw"
    """Continuous motion (like pressing arrow keys) to west until stop_motion is called."""

    @staticmethod
    def tracking(enabled: int) -> str:
        """
        Enable or disable tracking state.

        :param enabled: 0 to stop or 1 to start tracking (n).
        :return: STn.
        """

        if enabled not in (0, 1):
            raise WrongCommand("'tracking' must be 0 (stop) or 1 (start).")
        return f"ST{enabled}"

    @staticmethod
    def guide_north(ms: int) -> str:
        """
        Guide north for specified milliseconds.

        :param ms: an int (XXXXX) between 0 and 99999.
        :return: MnXXXXX.
        """

        if type(ms) is not int or not (0 <= ms <= 99999):
            raise WrongCommand("'guide_north' must be between 0 and 99999 ms.")
        return f"Mn{ms:05d}"

    @staticmethod
    def guide_east(ms: int) -> str:
        """
        Guide east for specified milliseconds.

        :param ms: an int (XXXXX) between 0 and 99999.
        :return: MeXXXXX.
        """

        if type(ms) is not int or not (0 <= ms <= 99999):
            raise WrongCommand("'guide_east' must be between 0 and 99999 ms.")
        return f"Me{ms:05d}"

    @staticmethod
    def guide_south(ms: int) -> str:
        """
        Guide south for specified milliseconds.

        :param ms: an int (XXXXX) between 0 and 99999.
        :return: MsXXXXX.
        """

        if type(ms) is not int or not (0 <= ms <= 99999):
            raise WrongCommand("'guide_south' must be between 0 and 99999 ms.")
        return f"Ms{ms:05d}"

    @staticmethod
    def guide_west(ms: int) -> str:
        """
        Guide west for specified milliseconds.

        :param ms: an int (XXXXX) between 0 and 99999.
        :return: MwXXXXX.
        """

        if type(ms) is not int or not (0 <= ms <= 99999):
            raise WrongCommand("'guide_west' must be between 0 and 99999 ms.")
        return f"Mw{ms:05d}"

    @staticmethod
    def custom_ra_rate(rate: float) -> str:
        """
        Set the Custom RA tracking rate (n.nnnn * sidereal rate).

        :param rate: a float (nnnnn) between 0.5000 and 1.5000.
        :return: RRnnnnn.
        """

        if not (0.5 <= rate <= 1.5):
            raise WrongCommand("'custom_ra_rate' must be between 0.5000 and 1.5000.")
        value = int(rate * 10000)
        return f"RR{value:05d}"
    
    # Position
    calibrate_mount = "CM"
    """Synchronize / calibrate mount."""
    set_zero = "SZP"
    """Set current position as zero position."""

    @staticmethod
    def set_ra(value: str) -> str:
        """
        Set Right Ascension.

        :param value: an 8 character string (XXXXXXXX).
        :return: SrXXXXXXXX.
        """

        if type(value) is not str or len(value) != 8:
            raise WrongCommand("'set_ra' requires an 8 character string.")
        return f"Sr{value}"

    @staticmethod
    def set_dec(value: str) -> str:
        """
        Set Declination.

        :param value: an 8 character string (TTTTTTTT).
        :return: SdsTTTTTTTT.
        """

        if type(value) is not str or len(value) != 8:
            raise WrongCommand("'set_dec' requires an 8 character string.")
        return f"Sds{value}"

    @staticmethod
    def set_altitude(value: str) -> str:
        """
        Set Altitude.

        :param value: an 8 character string (TTTTTTTT).
        :return: SasTTTTTTTT.
        """

        if type(value) is not str or len(value) != 8:
            raise WrongCommand("'set_altitude' requires an 8 character string.")
        return f"Sas{value}"

    @staticmethod
    def set_azimuth(value: str) -> str:
        """
        Set Azimuth.

        :param value: a 9 character string (TTTTTTTTT).
        :return: SzTTTTTTTT.
        """

        if type(value) is not str or len(value) != 9:
            raise WrongCommand("'set_azimuth' requires a 9 character string.")
        return f"Sz{value}"

    @staticmethod
    def set_parking_azimuth(value: str) -> str:
        """
        Set parking azimuth.

        :param value: a 9 character string (TTTTTTTTT).
        :return: SPATTTTTTTTT.
        """

        if type(value) is not str or len(value) != 9:
            raise WrongCommand("'set_parking_azimuth' requires a 9 character string.")
        return f"SPA{value}"

    @staticmethod
    def set_parking_altitude(value: str) -> str:
        """
        Set parking altitude.

        :param value: an 8 character string (TTTTTTTT).
        :return: SPHTTTTTTTT.
        """

        if type(value) is not str or len(value) != 8:
            raise WrongCommand("'set_parking_altitude' requires an 8 character string.")
        return f"SPH{value}"

    # Misc
    firmware_main_and_hc_date = "FW1"      
    """Get firmware date: mainboard & hand controller"""
    firmware_motor_date = "FW2"            
    """Get firmware date: RA & Dec motor boards"""
    mount_model = "MountInfo"              
    """Gets the mount model number"""


class IoptronCall:
    """
    Wrapper class to create a command call for RS-232 with the command.

    :param main_instance: The main class.
    :param commands: The class where the commands are translated.
    :param fast: True: no output returned; False: reads the output from the mount. Default: False.
    """

    def __init__(self, main_instance, commands, fast=False):
        """
        Initialize the class with the outer instances and 
        where to return or not the output of the mount.
        """
        
        if fast:
            self.send = main_instance.fast_send_cmd
        else:
            self.send = main_instance.send_cmd

        self.commands = commands

    def __getattr__(self, name):
        """
        Fallback from calling a non existing function in this class, and it will look up 
        in the commands class.

        :param name: Function name.
        """
        
        def call(*args):
            return self.send(cmd(*args))

        cmd = getattr(self.commands, name)
        if callable(cmd):
            return lambda *values: call(*values)
        else:
            return self.send(cmd)


class Ioptron(IoptronDevices, IoptronCommands):
    """
    Main class to bridge iOptron RS-232 Command Language with python calls

    :param IoptronDevices: Device list class.
    :param IoptronCommands: Command list class.
    :param port: The RS-232 port where the device is connected.
    """

    def __init__(self, port):
        """
        Initialize variables and define functions.
        """

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
        """
        Initialize the serial connection.

        :param timedate: If True, it will update the mount with the current computer date and time.
        :return: 1 if successful.
        """
        
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
        """
        Check if the mount is still connected. Raises an *MountConnectionError* error if not.
        
        :return: 1 if successful.
        """
        
        if self.device_num != self.send_cmd(self.mount_model):
            raise MountConnectionError("Health check failed.")
        else:
            return 1

    def close_serial(self):
        """
        Closes the serial connection.

        :return: 1 if successful.
        """
        
        self.device.close()
        return 1

    def send_cmd(self, data):
        """
        Send a string to the serial device and **read** its output. It encodes and decodes the string.

        :param data: The unencoded string.
        :return: The decoded output without *#*.
        """
        
        data = self.format_command(data)
        self.device.write(data.encode())
        time.sleep(0.01)
        line = self.device.read_until(b"#")
        return line.decode().strip("#")

    def fast_send_cmd(self, data):
        """
        Send a string to the serial **without** reading its output. It encodes the string.

        :param data: The unencoded string.
        :return: 1 after completion.
        """
        
        data = self.format_command(data)
        self.device.write(data.encode())
        return 1

    @staticmethod
    def format_command(data):
        """
        Format the input command and check for errors. It also **adds** *:* at the beginning 
        and *#* at the end of the command string.

        :param data: The unformatted command.
        :return: The formatted command.
        """
        
        if type(data) is not str:
            raise TypeError("Command should be a string.")
        elif " " in data:
            raise ValueError("Command should not have spaces.")
        return ":" + data + "#"

    def set_current_timedate(self):
        """
        Send the commands to update the date and time of the mount with the current computer time.
        """
        
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