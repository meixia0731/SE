import threading
import modbus_tk
import modbus_tk.defines as cst
import modbus_tk.modbus as modbus
import modbus_tk.modbus_tcp as modbus_tcp
import time
import random


modbus_slave_ip = "0.0.0.0"
modbus_slave_port = 502
modbus_slave_id = 1


Active_Power_Scaling = 100
Active_Power_SP_Scaling = 100

P_reading_scaling = 1
P_writing_scaling = 1

Active_Power_addr = [8069,0]
Reactive_Power_addr = [8075,10000]
Limitation_Power_addr = [8085,30000]
Start_Stop_Status_addr = [8067,1]
Start_Stop_Cmd_addr = [8002,1]
Active_Power_SP_addr = [8005,30000]

# Ramp_rate: 1 means percentage, 2 means fixed kw
Ramp_rate_type = 1
Ramp_rate_value = 5
Ramp_rate_percentage = 0.3

            
def PV_SIMULATOR():
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
    #Initialization

    Active_Power_MC = Converter(int(Active_Power_addr[1]/Active_Power_Scaling),64,1,2)
    Reactive_Power_MC = Converter(Reactive_Power_addr[1],64,1,1)
    Limitation_Power_MC = Converter(Limitation_Power_addr[1],32,1,2)
    Start_Stop_Status_MC = Converter(Start_Stop_Status_addr[1],16,1,2)
    Start_Stop_Cmd_MC = Converter(Start_Stop_Cmd_addr[1],16,1,2)
    Active_Power_SP_MC = Converter(int(Active_Power_SP_addr[1]/Active_Power_SP_Scaling),32,1,2)
    
    slave_1.set_values('A', Active_Power_addr[0], Active_Power_MC)
    slave_1.set_values('A', Reactive_Power_addr[0],Reactive_Power_MC)
    slave_1.set_values('A', Limitation_Power_addr[0],Limitation_Power_MC)
    slave_1.set_values('A', Start_Stop_Status_addr[0],Start_Stop_Status_MC)
    slave_1.set_values('B', Start_Stop_Cmd_addr[0],Start_Stop_Cmd_MC)
    slave_1.set_values('B', Active_Power_SP_addr[0],Active_Power_SP_MC)
    
    while True:
        Active_Power_INT = int(Converter(list(slave_1.get_values('A', Active_Power_addr[0], 4)),64,2,2)*Active_Power_Scaling)
        Reactive_Power_INT = Converter(list(slave_1.get_values('A', Reactive_Power_addr[0], 4)),64,2,1)
        Limitation_Power_INT = Converter(list(slave_1.get_values('A', Limitation_Power_addr[0], 2)),32,2,2)
        Start_Stop_Status_INT = Converter(list(slave_1.get_values('A', Start_Stop_Status_addr[0], 1)),16,2,2)
        Start_Stop_Cmd_INT = Converter(list(slave_1.get_values('B', Start_Stop_Cmd_addr[0], 1)),16,2,2)
        Active_Power_SP_INT = int(Converter(list(slave_1.get_values('B', Active_Power_SP_addr[0], 2)),32,2,2)*Active_Power_SP_Scaling)

        print('---------------------------------------------------------')
        print('Engine inputs:')
        print('Active_Power:',Active_Power_INT,'W')
        print('Reactive_Power:',Reactive_Power_INT,'Var')
        print('Limitation_Power:',Limitation_Power_INT,'W')
        print('Start_Stop_Status:',Start_Stop_Status_INT)
        print('Start_Stop_Cmd:',Start_Stop_Cmd_INT)
        print('Active_Power_SP:',Active_Power_SP_INT,'W')
        print('----------------')
        print('Engine Outputs:')        
        if Start_Stop_Cmd_INT == 0:
            Active_Power_INT =  int(((0 - Active_Power_INT)*Ramp_rate_percentage + Active_Power_INT)*random.uniform(0.98,1.02)/Active_Power_Scaling)
        else:
            Active_Power_INT =  int(((min(Active_Power_SP_INT,Limitation_Power_INT) - Active_Power_INT)*Ramp_rate_percentage + Active_Power_INT)*random.uniform(0.99,1.01)/Active_Power_Scaling)

        Active_Power_MC = Converter(Active_Power_INT,64,1,2)
        slave_1.set_values('A', Active_Power_addr[0], Active_Power_MC)
        print('Sent out Active_Power is', Active_Power_INT, 'kW','Scaling:',Active_Power_Scaling/1000)
        
        Reactive_Power_INT = random.randint(-1*Reactive_Power_addr[1],Reactive_Power_addr[1])
        Reactive_Power_MC = Converter(Reactive_Power_INT,64,1,1)
        slave_1.set_values('A', Reactive_Power_addr[0], Reactive_Power_MC)
        print('calculated Ractive_Power is', Reactive_Power_INT,'Var')                          
        print('')

        if Active_Power_INT == 0:
            Start_Stop_Status_INT = 0
        else:
            Start_Stop_Status_INT = 1
        Start_Stop_Status_MC = Converter(Start_Stop_Status_INT,16,1,2)        
        slave_1.set_values('A', Start_Stop_Status_addr[0], Start_Stop_Status_MC)
        
        time.sleep(1)


def Converter(number,index,direction,sign):
#index为该数据位宽,number为待转换数据,direction为转换方向(1为十进制转机器码，2为机器码转十进制),sign为输入或输出的机器码是否带符号(1为带符号，2为不带符号),
    result = []
    result1 = []
    if (direction == 1):#十进制转机器码
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
                b = '1' * (index+2 - len(b)) + b    #注意这里算出来的结果是补码
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
    elif(direction==2):#机器码转十进制
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
            if(number[0]>127):#如果首位是1
                j=-(2**index-j)
#                print(j)
                return j
            else:
#                print(j)
                return j
            
if __name__ == "__main__":
    PV_SIMULATOR()
