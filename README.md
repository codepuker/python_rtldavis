# python_rtldavis

## Brief Description
A python script which will call "rtldavis", decode the protocol, store data in a database and produce random errors.

## Long description
I'm very interested in wether data. Some days ago I noticed a weather station on the rooftop of my workplace. Unfortunately:
* it's very difficult to know who installed it and why;
* it's quite impossibile to have access to collected data

Being an SDR lover I searched the web to see if someone had written a program to receive Davis Instruments data, collect them and display on a web page. I found [rtldavis project] (https://github.com/bemasher/rtldavis) which is written in "go lang" and will perform following operation:
* bind to an rtl-sdr device, set the operating frequency, gain and sample rate;
* collect data implement frequency hopping;
* demodulate data;
* display raw data.
Protocol is not decoded, and no CRC is calculated, so raw data are "dirty" and may be corrupted.

## Code mods and hacking
rtldavis program is writte in go-lang and it was written with USA in mind: Frequencies coded are in the 915MHz band and will not fit an European installation. It is mandatory to modify the protocol.go file in order to put the right frequencies. The idea come from [thi article](https://github.com/bemasher/rtldavis/issues/3). 

## Python script
The idea of using python to manage rtldavis comes from [Jacardunio](https://github.com/jcarduino/rtl_433_2db). His code was slightly modified in order to fit my needs. Python script performs follwing operations:
* Start rtldavis program;
* Connect to database;
* Fetch last data and initialize variables;
* Get data from rtldavis and decode them [more information](https://github.com/dekay/DavisRFM69/wiki/Message-Protocol)
* Store data in a database

## Utils
Sometimes the main decoder will hang and stop inserting data in the database. So there is a "watch dog" that is run every 5 minutes and that will take care of python process. The process will be killed and restarted.

## What's in the package
What da ya want for nothing? ... a rrrrrrrrubber biscuit?
* Modified rtldavis code;
* Python code to run the script;
* Database schema;

## TO DO LIST
* Implement a CRC function to drop bad packets;
* Integrate everything in the main go lang program;
* Learn how to write better code.
