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
modbus_slave_ip = "172.168.200.4"
#Listening port
modbus_slave_port = 502
#Listening slave ID
modbus_slave_id = 255


# list[address,length,sign,default_value]
CB_Status_addr = [12000,16,2,5]
CB_Cmd_addr = [7999]


Status = {4:'Open',5:'Close'}

#------------------------------------------------------------------------------

def CB_SIMULATOR():
    #Create the server
    server = modbus_tcp.TcpServer(address=modbus_slave_ip, port=modbus_slave_port)
    #Start the server
    server.start()
    #Add slave
    slave_1 = server.add_slave(modbus_slave_id)
    
    #Add data blocks
    slave_1.add_block('A', cst.HOLDING_REGISTERS, 11999, 200)
    slave_1.add_block('B', cst.HOLDING_REGISTERS, 7999, 200)
    slave_1.add_block('C', cst.HOLDING_REGISTERS, 21190, 1)
    slave_1.add_block('D', cst.HOLDING_REGISTERS, 8871, 1)    
    slave_1.set_values('A', CB_Status_addr[0], CB_Status_addr[3])
    slave_1.set_values('C', 21190, 2)
    slave_1.set_values('D', 8871, 2)
    #Read cmd and generate feedback  
    while True:
        # Read data from memory, convert it from machine code to int. These values are input of the simulator engine
        CB_Status_INT = slave_1.get_values('A', CB_Status_addr[0],1)
        CB_Cmd_INT = slave_1.get_values('B', CB_Cmd_addr[0],6)
        
        print('---------------------------------------------------------')
        print('Engine inputs:')
        print('CB_Status:',Status[CB_Status_INT[0]])
        print(CB_Cmd_INT == (904,10,5377,1,13017,13017))
        print('CB_Cmd:',CB_Cmd_INT)
        print('----------------')
        print('Engine Outputs:')


        #if stop command received, change P setpoint to zero. New P = P + (P_setpint-P)*Ramprate
        if CB_Cmd_INT == (904,10,5377,1,13107,13107):
            CB_Status_INT = [4]
            slave_1.set_values('B', CB_Cmd_addr[0], [0]*6)
        elif CB_Cmd_INT == (905,10,5377,1,13107,13107):
            CB_Status_INT = [5]
            slave_1.set_values('B', CB_Cmd_addr[0], [0]*6)
        else:
            pass
        # Update P to memory
        slave_1.set_values('A', CB_Status_addr[0], CB_Status_INT)
        print('New CB_Status:',Status[CB_Status_INT[0]])      
        time.sleep(1)


            
if __name__ == "__main__":
    CB_SIMULATOR()
