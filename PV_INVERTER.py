import threading
import modbus_tk
import modbus_tk.defines as cst
import modbus_tk.modbus as modbus
import modbus_tk.modbus_tcp as modbus_tcp
import time
import random

#------------------------------------------------------------------------------

#Configuration:

#Listening IP address
modbus_slave_ip = "0.0.0.0"

#Listening port
modbus_slave_port = 502

#Listening slave ID
modbus_slave_id = 1


Active_Power_Scaling = 1
Active_Power_SP_Scaling = 1

P_reading_scaling = 1
P_writing_scaling = 1

# list[address,length,sign,default_value]
Active_Power_addr = [8069,64,2,0]
Reactive_Power_addr = [8075,64,1,10000]
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

def Generator_SIMULATOR():
    global Active_Power,Reactive_Power,Limitation_Power,Start_Stop_Status,Start_Stop_Cmd,Active_Power_SP
    #Create the server
    server = modbus_tcp.TcpServer(address=modbus_slave_ip, port=modbus_slave_port)
    
    #Start the server
    server.start()
    
    #Add slave
    slave_1 = server.add_slave(modbus_slave_id)
    
    #Add data blocks
    slave_1.add_block('A', cst.ANALOG_INPUTS, 8000, 150)
    slave_1.add_block('B', cst.HOLDING_REGISTERS, 8000, 10)
    
    #Initialization, convert data to machine code
    Active_Power_MC = Converter(int(Active_Power_addr[3]/Active_Power_Scaling),Active_Power_addr[1],1,Active_Power_addr[2])
    Reactive_Power_MC = Converter(Reactive_Power_addr[3],Reactive_Power_addr[1],1,Reactive_Power_addr[2])
    Limitation_Power_MC = Converter(Limitation_Power_addr[3],Limitation_Power_addr[1],1,Limitation_Power_addr[2])
    Start_Stop_Status_MC = Converter(Start_Stop_Status_addr[3],Start_Stop_Status_addr[1],1,Start_Stop_Status_addr[2])
    Start_Stop_Cmd_MC = Converter(Start_Stop_Cmd_addr[3],Start_Stop_Cmd_addr[1],1,Start_Stop_Cmd_addr[2])
    Active_Power_SP_MC = Converter(int(Active_Power_SP_addr[3]/Active_Power_SP_Scaling),Active_Power_SP_addr[1],1,Active_Power_SP_addr[2])
    Energy_MC = Converter(Energy_addr[1],Energy_addr[1],1,Energy_addr[2])
    
    slave_1.set_values('A', Active_Power_addr[0], Active_Power_MC)
    slave_1.set_values('A', Reactive_Power_addr[0],Reactive_Power_MC)
    slave_1.set_values('A', Limitation_Power_addr[0],Limitation_Power_MC)
    slave_1.set_values('A', Start_Stop_Status_addr[0],Start_Stop_Status_MC)
    slave_1.set_values('A', Energy_addr[0],Energy_MC)
    slave_1.set_values('B', Start_Stop_Cmd_addr[0],Start_Stop_Cmd_MC)
    slave_1.set_values('B', Active_Power_SP_addr[0],Active_Power_SP_MC)

    #Read sepoint and generate feedback    
    while True:
        # Read data from memory, convert it from machine code to int. These values are input of the simulator engine
        Active_Power_INT = int(Converter(list(slave_1.get_values('A', Active_Power_addr[0], int(Active_Power_addr[1]/16))),Active_Power_addr[1],2,Active_Power_addr[2])*Active_Power_Scaling)
        Reactive_Power_INT = Converter(list(slave_1.get_values('A', Reactive_Power_addr[0], int(Reactive_Power_addr[1]/16))),Reactive_Power_addr[1],2,Reactive_Power_addr[2])
        Limitation_Power_INT = Converter(list(slave_1.get_values('A', Limitation_Power_addr[0], int(Limitation_Power_addr[1]/16))),Limitation_Power_addr[1],2,Limitation_Power_addr[2])
        Start_Stop_Status_INT = Converter(list(slave_1.get_values('A', Start_Stop_Status_addr[0], int(Start_Stop_Status_addr[1]/16))),Start_Stop_Status_addr[1],2,Start_Stop_Status_addr[2])
        Start_Stop_Cmd_INT = Converter(list(slave_1.get_values('B', Start_Stop_Cmd_addr[0], int(Start_Stop_Cmd_addr[1]/16))),Start_Stop_Cmd_addr[1],2,Start_Stop_Cmd_addr[2])
        Active_Power_SP_INT = int(Converter(list(slave_1.get_values('B', Active_Power_SP_addr[0], int(Active_Power_SP_addr[1]/16))),Active_Power_SP_addr[1],2,Active_Power_SP_addr[2])*Active_Power_SP_Scaling)
        Energy_INT = Converter(list(slave_1.get_values('A', Energy_addr[0], int(Energy_addr[1]/16))),Energy_addr[1],2,Energy_addr[2])
        
        print('---------------------------------------------------------')
        print('Engine inputs:')
        print('Active_Power:',Active_Power_INT,'W')
        print('Reactive_Power:',Reactive_Power_INT,'Var')
        print('Limitation_Power:',Limitation_Power_INT,'W')
        print('Start_Stop_Status:',Start_Stop_Status_INT)
        print('Start_Stop_Cmd:',Start_Stop_Cmd_INT)
        print('Active_Power_SP:',Active_Power_SP_INT,'W')
        print('Energy:',Energy_INT,'W')
        print('----------------')
        print('Engine Outputs:')

        #if stop command received, change P setpoint to zero. New P = P + (P_setpint-P)*Ramprate
        if Start_Stop_Cmd_INT == 0:
            Active_Power_INT =  int(((0 - Active_Power_INT)*Ramp_rate_percentage + Active_Power_INT)*random.uniform(0.98,1.02)/Active_Power_Scaling)
        else:
            Active_Power_INT =  int(((min(Active_Power_SP_INT,Limitation_Power_INT) - Active_Power_INT)*Ramp_rate_percentage + Active_Power_INT)*random.uniform(0.99,1.01)/Active_Power_Scaling)

        # Converter P to machine code
        Active_Power_MC = Converter(Active_Power_INT,Active_Power_addr[1],1,Active_Power_addr[2])
        # Update P to memory
        slave_1.set_values('A', Active_Power_addr[0], Active_Power_MC)
        print('Sent out Active_Power is', Active_Power_INT, 'kW','Scaling:',Active_Power_Scaling)
        # Generate new Q       
        Reactive_Power_INT = random.randint(-1*Reactive_Power_addr[1],Reactive_Power_addr[1])
        # Converter Q to machine code
        Reactive_Power_MC = Converter(Reactive_Power_INT,Reactive_Power_addr[1],1,Reactive_Power_addr[2])
        # Update Q to memory
        slave_1.set_values('A', Reactive_Power_addr[0], Reactive_Power_MC)
        print('calculated Ractive_Power is', Reactive_Power_INT,'Var')


        # Generate new Energy
        Energy_INT = Energy_INT + 1
        # Converter Energy to machine code
        Energy_MC = Converter(Energy_INT,Energy_addr[1],1,Energy_addr[2])
        # Update Energy to memory
        slave_1.set_values('A', Energy_addr[0], Energy_MC)
        print('calculated Energy', Energy_INT,'kWh')  
        print('')

        # If Active_Power = 0 ,change status to stopped
        if Active_Power_INT == 0:
            Start_Stop_Status_INT = 0
        else:
            Start_Stop_Status_INT = 1
        Start_Stop_Status_MC = Converter(Start_Stop_Status_INT,Start_Stop_Status_addr[1],1,Start_Stop_Status_addr[2])        
        slave_1.set_values('A', Start_Stop_Status_addr[0], Start_Stop_Status_MC)
        
        time.sleep(1)


def Converter(number,index,direction,sign):
#index is length:16,32,64; number is the data to be converted; direction(1:to machine code，2: from machine code);sign: 1 for signed, 20 for unsigned;
    result = []
    result1 = []
    if (direction == 1):
        if sign ==1:
            if index == 16 and (number > 32767 or number < -32768):
                print('MAX int16 is -32768~ +32767')
                return
            elif index == 32 and (number > 2147483647 or number < -2147483648):
                print('MAX int32 is -2,147,483,648 ~ +2,147,483,647')
                return
            elif index == 64 and (number > 9223372036854775807  or number < -9223372036854775808):
                print('MAX int64 is -9,223,372,036,854,775,808 ~ +9,223,372,036,854,775,807 ')
                return
            if(number >= 0):
                b=bin(number)
                b = '0' * (index+2 - len(b)) + b
            else:
                b=2**(index)+number
                b=bin(b)
                b = '1' * (index+2 - len(b)) + b
            b=b.replace("0b",'')
            b=b.replace('-','')
            for i in range(int(index/8)):
                result.append(int(b[0:8],2))
                b=b[8:]
            for i in range(int(len(result)/2)):
                result1.append(result[0]*256+result[1])
                result = result[2:]
            return result1
        elif sign ==2:
            if(number >= 0):
                b=bin(number)
                b = '0' * (index+2 - len(b)) + b
            else:
                print('Input must be positive')
                return
            b=b.replace("0b",'')
            for i in range(int(index/8)):
                result.append(int(b[0:8],2))
                b=b[8:]
            for i in range(int(len(result)/2)):
                result1.append(result[0]*256+result[1])
                result = result[2:]
#            print(result1)
            return result1          
    elif(direction==2):
        j=''
        if sign ==2:
            for i in range(len(number)):
                j = j + '{:0>4x}'.format(number[i])
            j=int(j,16)
#            print(j)
            return j
        elif sign ==1:
            for i in range(len(number)):
                j = j + '{:0>4x}'.format(number[i])
            j=int(j,16)
            if(number[0]>127):
                j=-(2**index-j)
#                print(j)
                return j
            else:
#                print(j)
                return j
            
if __name__ == "__main__":
    Generator_SIMULATOR()
