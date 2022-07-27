import threading
import modbus_tk
import modbus_tk.defines as cst
import modbus_tk.modbus as modbus
import modbus_tk.modbus_tcp as modbus_tcp
import time


modbus_slave_ip = "172.168.200.8"
modbus_slave_port = 502
modbus_slave_id = 1
value1 = [1]
def PV_SIMULATOR():    
    #Create the server
    server = modbus_tcp.TcpServer(address=modbus_slave_ip, port=modbus_slave_port)
    #Start the server
    server.start()
    #Add slave
    slave_1 = server.add_slave(modbus_slave_id)
    #Add data blocks
    slave_1.add_block('A', cst.HOLDING_REGISTERS, 8004, 2)
    slave_1.add_block('B', cst.ANALOG_INPUTS, 8069, 4)
    slave_1.add_block('C', cst.ANALOG_INPUTS, 8075, 4)
    slave_1.add_block('D', cst.ANALOG_INPUTS, 8067, 1)


    while True:
        slave_1.set_values('A', 8005, value1)
        slave_1.set_values('B', 8072, value1)
        slave_1.set_values('C', 8078, value1)
        value1[0] = value1[0] + 1
        if value1[0]%2 == 0:
            slave_1.set_values('D', 8067, [0])
        else:
            slave_1.set_values('D', 8067, [1])
            
        time.sleep(2)
    
if __name__ == "__main__":
    PV_SIMULATOR()
