import threading
import modbus_tk
import modbus_tk.defines as cst
import modbus_tk.modbus as modbus
import modbus_tk.modbus_tcp as modbus_tcp
import time


modbus_slave_ip = "0.0.0.0"
modbus_slave_port = 502
modbus_slave_id = 1
modbus_slave_start_addr = 0

modbus_master_ip = "192.168.3.36"
modbus_master__port = 502
modbus_master__id = 1
modbus_master__start_addr = 0

reconnection = 5

def f6_to_f5():    
    #Create the server
    server = modbus_tcp.TcpServer(address=modbus_slave_ip, port=modbus_slave_port)
    #Start the server
    server.start()
    #Add slave
    slave_1 = server.add_slave(modbus_slave_id)
    #Add data block 'A'
    slave_1.add_block('A', cst.HOLDING_REGISTERS, modbus_slave_start_addr, 1)
    #Create the master    
    master = modbus_tcp.TcpMaster(host=modbus_master_ip, port=modbus_master__port)
    master.set_timeout(5.0)

    while True:
        try:
            value1 = slave_1.get_values('A', modbus_slave_start_addr, 1)
            time.sleep(1)
            value2 = slave_1.get_values('A', modbus_slave_start_addr, 1)
            if value1[0] == value2[0] or value2[0] == 0:
                print('No change,Continue')
                continue
            else:
                print('Data changed, Forwarding')
                master.execute(modbus_master__id, cst.WRITE_SINGLE_COIL, value2[0], output_value=1)
##            if value[0] == 4:
##                master.execute(modbus_master__id, cst.WRITE_SINGLE_COIL, modbus_master__start_addr, output_value=1)
##            else:
##                master.execute(modbus_master__id, cst.WRITE_SINGLE_COIL, modbus_master__start_addr, output_value=0)
        except:
                master = modbus_tcp.TcpMaster(host=modbus_master_ip, port=modbus_master__port)
                master.set_timeout(5.0)
##                reconnection = reconnection*2
                time.sleep(reconnection)
        else:
##            reconnection = 2
            continue
if __name__ == "__main__":
    f6_to_f5()
