# Please create a mysql database for user rtl433db with create rights so table can be created
# change ip for database server
# install mysql connector
# install phython 2.7
# let it run ;)
#!/usr/bin/python
#import sys
import subprocess
import time
import threading
import Queue
import mysql.connector
import json
import re
import sys
from mysql.connector import errorcode

config = {
  'user': 'tempo',
  'password': 'tempo_pass',
  'host': 'localhost',
  'database': 'weather',
  'raise_on_warnings': True,
}

line = ""
output = ""
wind_velocity = 0
wind_direction_dec = 0
wind_gust = 0
rain = 0
humidity = 0
wind_gust = 0
rainrate = 0
solar_radiation = 0
temperature = 0
uvindex = 0
supercap = 0


class AsynchronousFileReader(threading.Thread):
    '''
    Helper class to implement asynchronous reading of a file
    in a separate thread. Pushes read lines on a queue to
    be consumed in another thread.
    '''

    def __init__(self, fd, queue):
        assert isinstance(queue, Queue.Queue)
        assert callable(fd.readline)
        threading.Thread.__init__(self)
        self._fd = fd
        self._queue = queue

    def run(self):
        '''The body of the tread: read lines and put them on the queue.'''
        for line in iter(self._fd.readline, ''):
            self._queue.put(line)

    def eof(self):
        '''Check whether there is no more content to expect.'''
        return not self.is_alive() and self._queue.empty()

def replace(string):
    while '  ' in string:
        string = string.replace('  ', ' ')
    return string

def truncate(f_number, n_decimals):
      strFormNum = "{0:." + str(n_decimals+5) + "f}"
      trunc_num = float(strFormNum.format(f_number)[:-5])
      return(trunc_num)

def zero():
    return '0'
def one():
    return '1'
def two():
    global supercap
    value = ((int(output[3],16) * 0x04) + ((int(output[4],16) & 0xC0) / 0x40)) / 0x64
    supercap = int(value)
    return '2'
def three():
    return '3'
def four():
    global uvindex
    value = ((int(output[3],16) << 8) + int(output[4],16) >> 6) / 0x32
    uvindex = int(value)
    return value
def five():
    global rainrate
    if (int(output[3],16) == 0xFF):
        value = 0
    elif ((int(output[4],16) & 0x40) == 0): #light rain
        time_clicks = (((int(output[4],16) & 0x30) / 0x10 * 0xfa) + int(output[3],16))
        value = 0x2d0 / (((int(output[4],16) & 0x30) / 0x10 * 0xfa) + int(output[3],16))
    elif ((int(output[4],16) & 0x40) == 0x40):
        time_clicks = (((int(output[4],16) & 0x30) / 0x10 * 0xfa) + int(output[3],16)) / 0x10
        value = 0x2d00 / (((int(output[4],16) & 0x30) / 0x10 * 0xfa) + int(output[3],16))
    rainrate=float(value)/1000*25.4    
    return value
def six():
    global solar_radiation
    value = float((((int(output[3],16) << 8) + int(output[4],16)) >> 6)) * 1.757936
    solar_radiation=truncate(value,2)
    return value
def seven():
    return '7'
def eight():
    global temperature
    value = ( int(output[3],16) * 256 + int(output[4],16) ) / 160
    value = truncate(float(((int(value))-32.0) * 5.0 / 9.0),2)
    temperature = value
    return value
def nine():
    global wind_gust
    if (output[3] != 0):
        value = truncate(( float(int(output[3],16) & 0xf0 >> 4 )) * 1.60934)
    wind_gust=value
    return value
def ten():
    global humidity
    value = (((int(output[4],16) >> 4) << 8) + int(output[3],16)) / 0x0a
    humidity=int(value)
    return value
def fifteen():
    global rain
    if (int(output[3],16) == 0x80):
        value=0
    else:
        value=int(output[3],16)
    	value=value/1000
	value=value*2.54
    rain=float(value)
    return value 

def message_decode(i):
    print("decode input")
    print(output)
    switcher={
             '0':zero,
             '1':one,
             '2':two,     #supercap
             '3':three,
             '4':four,    #UV index
             '5':five,    #Rain Rate
             '6':six,     #Solar Radiation
             '7':seven,   #Solar Cell Output
             '8':eight,   #Temperature
             '9':nine,    #Wind Gust
             'A':ten,     #Humidity
             'E':fifteen #Rain
             }
    func=switcher.get(i,"Invalido")
    print func()
    func()




def startsubprocess(command):
    '''
    Example of how to consume standard output and standard error of
    a subprocess asynchronously without risk on deadlocking.
    '''
    global output
    global wind_velocity 
    global wind_direction_dec 
    global wind_gust 
    global rain 
    global humidity 
    global wind_gust 
    global rainrate 
    global solar_radiation 
    global temperature 
    global uvindex 
    global supercap 
   
    
    print "\n\nStarting sub process " + command + "\n"
    # Launch the command as subprocess.

    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)

    # Launch the asynchronous readers of the process' stdout and stderr.
    stdout_queue = Queue.Queue()
    stdout_reader = AsynchronousFileReader(process.stdout, stdout_queue)
    stdout_reader.start()
    stderr_queue = Queue.Queue()
    stderr_reader = AsynchronousFileReader(process.stderr, stderr_queue)
    stderr_reader.start()
    # do database stuff init
    try:    
        print("Connecting to database")
        cnx = mysql.connector.connect(**config)
        print("Connection ok")
    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            print("Something is wrong with your user name or password")
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            print("Database does not exists, please create it before using this script.")
        else:
            print(err) 
    cursor = cnx.cursor()    
    
    #Executing a query to valorize variables with last known data. "zero-bug" correction
    print("Esecuzione della query")    
    try:    
        start_query= ("select wind_velocity,wind_direction,wind_gust,rain_rate,rain,humidity,temperature,solar_index,uv_index,supercap from meteo_temp where id=(select max(id) from meteo_temp)")
        cursor.execute(start_query)
        row = cursor.fetchall()
        result_row=row[0]
        
        wind_velocity = result_row[0]
        wind_direction_dec = result_row[1]
        wind_gust = result_row[2]
        rainrate = result_row[3]
        rain = result_row[4]
        humidity = result_row[5]
        temperature = result_row[6]
        solar_radiation = result_row[7]
        uvindex = result_row[8]
        supercap = result_row[9]
        
        print("DB - velocita %s" %wind_velocity)
        print("DB - direzione %s" %wind_direction_dec)
        print("DB - rafficaa %s" %wind_gust)
        print("DB - rateo pioggia %s" %rainrate)
        print("DB - valore pioggia %s" %rain)
        print("DB - umnidita %s" %humidity)
        print("DB - temperatura %s" %temperature)
        print("DB - radiazione solare %s" %solar_radiation)
        print("DB - indice UV %s" %uvindex)
        print("DB - supercap %s" %supercap)
        
    except mysql.connector.Error as err:
        print(err) 
        cnx.reconnect() 
    
    while True:
        #file_log=open('/var/log/rtl_433.log','a')
        line = stdout_queue.get()
        #file_log.write(repr(line))
        with open('/var/log/rtlsdr3.log','a') as file_log:
            print >> file_log,line            
        #print("Ingresso %s" %(line))
        year, month, day, hour, minute, seconds = time.strftime("%Y,%m,%d,%H,%M,%S").split(',')
        print("Data %s %s %s Ora: %s %s %s" %( year,month,day,hour,minute,seconds))
        inputline  = line
        print(inputline)
        parts = inputline.split()
        print("Input Lenght %s" % (len(parts)))
        if len(parts) == 0:
            sys.exit()
        if len(parts) == 2:
            print("Colonna")
            print parts[1]
            line=parts[1]
            with open('/var/log/davis.log','a') as file_log:
                print >> file_log,line  
            n = 2
            output = [line[i:i+n] for i in range(0, len(line), n)]
            print("Output Lenght %s" %(len(output)))
            if len(output) < 8:
               print("Discard")
            else:        
               print (output)
               print ("Element 0 %s" % (output[0]))
               print ("Element 1 %s" % (output[1]))
               print ("Element 2 %s" % (output[2]))
               print ("Element 3 %s" % (output[3]))
               print ("Element 4 %s" % (output[4]))
               print ("Element 5 %s" % (output[5]))
               print ("Element 6 %s" % (output[6]))
               print ("Element 7 %s" % (output[7]))
               print ("\n")
              
               #Wind COnversion
               print("Wind Conversion")
               decimal_conv=int(output[1],16)
               print("Wind decimal conv %s" % (decimal_conv))
               wind_velocity=truncate(int(int(output[1],16))* 1.60934,2)
               print("Wind Velocity %s" % (wind_velocity))
               print ("\n")
    
               #Wind Direction Conversion
               print("Wind Direction Conversion")
               decimal_conv=int(output[2],16)
               print("Wind directiondecimal conv %s" % (decimal_conv))
               wind_direction_dec=int(output[2],16)
               if ( output[2] == 00 ):
                wind_direction = 360
               else: 
                   wind_direction = 9 + round(wind_direction_dec - 1) * 342.0 / 255.0
                   wind_direction = truncate(wind_direction, 2)
                   print("Wind Direction %s" % (wind_direction))
                   print ("\n")
        
                   #Message Type Elaboration
                   mtype=line[0]
                   print("Message Type %s" % (mtype))
                   station_id=int(int(line[1],16)) >> 4
                   print("Station id %s" % (station_id))
                   print ("\n")
    
                   print("Message Decode Function")
                   print(output)
                   message_decode(line[0])
    
                   print ("Summary")
                   print("Station id %s" % (station_id))
                   print("Message Type %s" % (mtype))
                   if   ( mtype == "2"):
                    print("Message Type SuperCap")
                   elif ( mtype == "4"):
                    print("Message Type UV Index")
                   elif ( mtype == "5"):
                    print("Message Type Rain Rate")
                   elif ( mtype == "6"):
                    print("Message Type Solar Radiation")
                   elif ( mtype == "7"):
                    print("Message Type Solar Cell Output")
                   elif ( mtype == "8"):
                    print("Message Type Temperature")
                   elif ( mtype == "9"):
                    print("Message Type Wind Gust")
                   elif ( mtype == "A"):
                    print("Message Type Humidity")
                   elif ( mtype == "E"):
                    print("Message Type Rain")
                   print("\n")
                   print("Wind Velocity %s" % (wind_velocity))
                   print("Wind Direction %s" % (wind_direction))
                   print("Wind Gust %s" % (wind_gust))
                   print("Humidity %s" % (humidity))
                   print("Rain %s" % (rain))
                   print("Rain Rate mm/h %s" % (rainrate))
                   print("Temperature C %s" % (temperature))
                   print("Solar Radiation %s" % (solar_radiation))
                   print("UV Index %s" % (uvindex))
                   print("SuperCap %s" % (supercap))
                   print ("\n")
                   mtype=int(mtype,16);
                   try:
                    print("Debug inserimento dati nel DB")
                    print("Debug - anno: %s" % (year))
                    add_sensordata= ("INSERT INTO meteo_temp (station_id,type,wind_velocity,wind_direction,wind_gust,rain_rate,rain,humidity,temperature,solar_index,uv_index,supercap) VALUES (%s, %s, %s, %s,%s, %s, %s, %s,%s, %s, %s, %s)")
                    sensordata = (station_id,int(mtype),wind_velocity,wind_direction,wind_gust,rainrate,rain,humidity,temperature,solar_radiation,uvindex,supercap)
                    cursor.execute(add_sensordata,sensordata)
                    add_sensordata= ("INSERT INTO meteo_2019 (station_id,type,wind_velocity,wind_direction,wind_gust,rain_rate,rain,humidity,temperature,solar_index,uv_index,supercap) VALUES (%s, %s, %s, %s,%s, %s, %s, %s,%s, %s, %s, %s    )")
                    sensordata = (station_id,int(mtype),wind_velocity,wind_direction,wind_gust,rainrate,rain,humidity,temperature,solar_radiation,uvindex,supercap)
                    cursor.execute(add_sensordata,sensordata)
                    cnx.commit()
                    file_log.close()
                   except mysql.connector.Error as err:
                    print(err) 
                    cnx.reconnect()
    stdout_reader.join()
    stderr_reader.join()

    # Close subprocess' file descriptors.
    process.stdout.close()
    process.stderr.close()
    
    
if __name__ == '__main__':
    # The main flow:
    #check if database is present, create tablesif no tables present
    print("Inizia")
    year, month, day, hour, minute = time.strftime("%Y,%m,%d,%H,%M").split(',')
    startsubprocess("rtldavis 2>&1")
    print("Closing down")
    
    
