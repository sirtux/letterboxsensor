# LoRaWAN EU868Mhz Letterbox Sensor

sensing letters in your letterbox via two infrared proximity sensors (HSDL9100),
sending out status via lora / lorawan, using RAK3172 (based on STM32WLE5CC) CPU/RF, powered by a CR2032 battery.

This project is a remake of https://github.com/hierle/letterbox-sensor-v2/, many thanks to the original author!

This design is built in a way, that it can be assembled by a factory house like JLCPCB and you do not need
to fiddle around with soldering small components - especially the HSDL9100 are very fiddly.


![LoRaWAN Letterbox Sensor PCB](https://github.com/sirtux/letterboxsensor/blob/main/pcb-front.png?raw=true)

Contents:

- ./letterboxsensor/		kicad design files
- ./jlclib/			library files for non standard components
- ./ttn/			Tools to setup TheThingsNetwork
- ./arduino/			Source Code for the sensor
- ./gerber/			Required files for PCB manufacturing
- ./jlcassembly/		Files for JLC Assembly Service

Features:
- using RAKWireless RAK3172 based on STM32WLE5CC
- deep sleep at (measured) 5uA including battery voltage divider and tantalium caps
- two proximity sensors HSDL9100
- USB-C interface for flashing and serial monitor, via FT230XS-R USB-UART
- onboard 868MHz PCB antenna after TI document http://www.ti.com/lit/an/swra227e/swra227e.pdf
- lorawan activation either ABP or OTAA
- battery voltage measurment thru voltage divider (2x 10MOhm)

RAK3172 documentation:

https://docs.rakwireless.com/Product-Categories/WisDuo/RAK3172-Module/Overview/


How to compile:

Follow the instructions on<br>
https://docs.rakwireless.com/Product-Categories/WisDuo/RAK3172-Module/Quickstart/<br>
in short:<br>
- install ArduinoIDE from arduino.cc
- add the following URL to the boards manager URLs section in preferences:
https://raw.githubusercontent.com/RAKWireless/RAKwireless-Arduino-BSP-Index/main/package_rakwireless.com_rui_index.json
- install the "RAKwireless RUI STM32 Boards" from the Boards Manager
- select "WisDuo RAK3172 Evaluation Board" board
- on Mac you might need to install pyserial: sudo pip3 install pyserial
- on Linux you might need to install python3-pyserial
- connect the board, make sure it's powered on (DIP switch)
- select the corresponding serial port
- open the sketch folder
- adjust config.h and lorawan.h
- compile and flash


For configuration adjust config.h and lorawan.h

config.h:
- PERIOD: the time intervall you want the sensor to send it's data, in minutes, default is 30 minutes
- THRESHOLD: the threshold for the sensor readings (empty/full), can later be "overwritten" in e.g. HTML integration
- USE_OTAA: if true, OTAA will be used instead of ABP, so we do not have to worry about frame counters after reset / battery change
- DATARATE and TXPOWER: adjust to your needs, your packets should be reliably received, w/o wasting to much power
- see also the comments for each entry in config.h

lorawan.h:
- set your lorawan keys for either ABP or OTAA
- OTAA_APPEUI or JOINEUI is only needed to select a specific JOIN server, in private networks can be set to any value


Additional notes:
- you will need a *DATA* USB-C cable, a charging only cable will not work, as it's missing the data pins ;-)
- the DIP switch allows to power the device directly from USB, but when using the battery in production environment (letterbox), it should be switched off, not to waist power on the FT230 USB-UART chip


Letterbox sensor v2 lorawan payload package byte structure:

|byte|    0     |  1   2 | 3   4 | 5   6 |    7    |
|----|----------|--------|-------|-------|---------|
|    |0x00=empty|battery |sensor1|sensor2|threshold|
|    |0xFF=full |voltage |raw    |raw    |         |
