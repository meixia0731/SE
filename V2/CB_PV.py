import time
import modbus_tk.defines as cst
import modbus_tk.modbus_tcp as modbus_tcp
from multiprocessing import Process
import datetime
import psycopg2
import random
from multiprocessing import shared_memory

# ------------------------------------------------------------------------------

# Configuration:

# Listening IP address
modbus_slave_ip_cb_pv = "172.168.200.3"
# Listening port
modbus_slave_port = 502
# Listening slave ID
modbus_slave_id = 255
# list[address,length,sign,default_value]
CB_Status_addr = [12000, 16, 2, 5]
CB_Cmd_addr = [7999]
Voltage_addr = [12029,230]
P_addr = [12040,1000]
Q_addr = [12044,2]
# CB type
CB = {'NSX': 4353, 'MTZ2': 5377}
Status = {4: 'Open', 5: 'Close'}

# ------------------------------------------------------------------------------

def CB_SIMULATOR(modbus_slave_ip, cb_type):
    # Connect to the log database
    conn = psycopg2.connect(dbname="microgrid", user="postgres",password="postgres", host="127.0.0.1", port="5432")
    cur = conn.cursor()
    # Create the server
    server = modbus_tcp.TcpServer(address=modbus_slave_ip, port=modbus_slave_port)
    # Start the server
    server.start()
    # Add slave
    slave_1 = server.add_slave(modbus_slave_id)
    # Add data blocks
    slave_1.add_block('A', cst.HOLDING_REGISTERS, 11999, 200)
    slave_1.add_block('B', cst.HOLDING_REGISTERS, 7999, 200)
    slave_1.add_block('C', cst.HOLDING_REGISTERS, 21190, 1)
    slave_1.add_block('D', cst.HOLDING_REGISTERS, 8871, 1)
    slave_1.set_values('A', CB_Status_addr[0], CB_Status_addr[3])
    slave_1.set_values('C', 21190, 2)
    slave_1.set_values('D', 8871, 2)
    # Created a shared memory to talk with BESS controller
    shm = shared_memory.SharedMemory(name=modbus_slave_ip,create=True, size=10)
    while True:
        # Read data from memory, convert it from machine code to int. These values are inputs of the simulator engine
        cb_status_int = slave_1.get_values('A', CB_Status_addr[0], 1)
        cb_cmd_int = slave_1.get_values('B', CB_Cmd_addr[0], 6)
        # if stop command received, change P setpoint to zero. New P = P + (P_setpint-P)*Ramprate
        if cb_cmd_int == (904, 10, CB[cb_type], 1, 13107, 13107):
            cb_status_int = [4]
            print(modbus_slave_ip, 'Open command received:', datetime.datetime.now())
            cur.execute(
                "INSERT INTO sim_log values(DEFAULT,now(),'{}','control_command_received_{}')".format(modbus_slave_ip,cb_cmd_int[0]))
            conn.commit()
            slave_1.set_values('B', CB_Cmd_addr[0], [0] * 6)
            print(modbus_slave_ip, 'Open command executed:', datetime.datetime.now())
        elif cb_cmd_int == (905, 10, CB[cb_type], 1, 13107, 13107):
            cb_status_int = [5]
            print(modbus_slave_ip, 'Close command received', datetime.datetime.now())
            cur.execute(
                "INSERT INTO sim_log values(DEFAULT,now(),'{}','control_command_received_{}')".format(modbus_slave_ip,cb_cmd_int[0]))
            conn.commit()
            slave_1.set_values('B', CB_Cmd_addr[0], [0] * 6)
            print(modbus_slave_ip, 'Close command executed', datetime.datetime.now())
        else:
            pass
        shm.buf[0] = cb_status_int[0]
        if cb_status_int[0] == 4:
            slave_1.set_values('A', P_addr[0], 0)
            slave_1.set_values('A', Q_addr[0], 0)
        elif cb_status_int[0] == 5:
            slave_1.set_values('A', Q_addr[0], int(Q_addr[1]*random.uniform(0.98, 1.02)))
            p = 1000*shm.buf[1] + shm.buf[2]
            slave_1.set_values('A', P_addr[0], p)
        slave_1.set_values('A', CB_Status_addr[0], cb_status_int)
        slave_1.set_values('A', Voltage_addr[0], Voltage_addr[1])
        time.sleep(0.1)


if __name__ == "__main__":
    CB_SIMULATOR(modbus_slave_ip_cb_pv,'MTZ2')