import threading
import modbus_tk
import modbus_tk.defines as cst
import modbus_tk.modbus as modbus
import modbus_tk.modbus_tcp as modbus_tcp
import time
import random
import struct

#--------------------------------------------------------------------t 
modbus_slave_ip = '0.0.0.0'
#Listening port
modbus_slave_port = 502

#Listening slave ID
modbus_slave_id = 1


Active_Power_Scaling = 1
Active_Power_SP_Scaling = 1


# list[address,length,sign,default_value]
Active_Power_addr= [8069,'uint64',65536]
Reactive_Power_addr = [8075,'int64',10000]
Limitation_Power_addr = [8085,32,2,30000]
Start_Stop_Status_addr = [8067,16,2,21]
Start_Stop_Cmd_addr = [8002,16,2,1]
Active_Power_SP_addr = [8005,32,2,30000]
Energy_addr = [8079,64,2,0]

# Ramp_rate: 1 means percentage, 2 means kw
Ramp_rate_type = 1
Ramp_rate_value = 5
Ramp_rate_percentage = 0.3

#------------------------------------------------------------------------------

def PV_SIMULATOR():
    #Create the server
    server = modbus_tcp.TcpServer(address=modbus_slave_ip, port=modbus_slave_port)    
    server.start()
    
    #Add slave
    slave_1 = server.add_slave(modbus_slave_id)
    
    #Add data blocks
    slave_1.add_block('A', cst.ANALOG_INPUTS, 8000, 150)
    slave_1.add_block('B', cst.HOLDING_REGISTERS, 8000, 10)
    
    #Initialization, convert data to machine code  
    Active_Power_C = int2C(Active_Power_addr[1],Active_Power_addr[2])
    print(Active_Power_C)
    slave_1.set_values('A', Active_Power_addr[0], Active_Power_C)

    #Read sepoint and generate feedback    
    while True:
        # Read data from memory, convert it from machine code to int. These values are input of the simulator engine
        Active_Power_C = slave_1.get_values('A',Active_Power_addr[0],4)
        print(Active_Power_C)
        Active_Power_INT = C2int(Active_Power_addr[1],Active_Power_C)
        print(Active_Power_INT)        

        Active_Power_INT = random.randrange(1,999999999999)
        print(Active_Power_INT)
        Active_Power_C = int2C(Active_Power_addr[1],Active_Power_INT)
        print(Active_Power_C)
        slave_1.set_values('A', Active_Power_addr[0], Active_Power_C)

        time.sleep(2)
        print('--------------------------------')
        #if stop command received, change P setpoint to zero. New P = P + (P_setpint-P)*Ramprate
 #       if Start_Stop_Cmd_INT == 0:
 #           Active_Power_INT =  int(((0 - Active_Power_INT)*Ramp_rate_percentage + Active_Power_INT)*random.uniform(0.98,1.02)/Active_Power_Scaling)
 #       else:
 #           Active_Power_INT =  int(((min(Active_Power_SP_INT,Limitation_Power_INT) - Active_Power_INT)*Ramp_rate_percentage + Active_Power_INT)*random.uniform(0.99,1.01)/Active_Power_Scaling)

        # Converter P to machine code
 #       Active_Power_MC = Converter(Active_Power_INT,Active_Power_addr[1],1,Active_Power_addr[2])
        # Update P to memory
 #       slave_1.set_values('A', Active_Power_addr[0], Active_Power_MC)
 #       print('Sent out Active_Power is', Active_Power_INT, 'kW','Scaling:',Active_Power_Scaling)

def int2C(data_type,value):
    if data_type == 'uint64':
        value = struct.pack('>Q',value)
        return[value[0]*16+value[1],value[2]*16+value[3],value[4]*16+value[5],value[6]*16+value[7]]

def C2int(data_type,value):
    if data_type == 'uint64':
        bytes_value = struct.pack('>H',value[0]) + struct.pack('>H',value[1]) + struct.pack('>H',value[2]) + struct.pack('>H',value[3])
        value = struct.unpack('>Q',bytes_value)
        return value

if __name__ == "__main__":
    PV_SIMULATOR()
