import time
import modbus_tk.defines as cst
import modbus_tk.modbus_tcp as modbus_tcp
import datetime
import psycopg2
from data_type_converter import int2C as int2C
from data_type_converter import C2int as C2int
from multiprocessing import shared_memory

# ------------------------------------------------------------------------------
# Configuration:
# Listening IP address
modbus_slave_ip_pv = '172.168.200.8'
# PV_CB address. PV will get CB status from this memory and send P to this memory
modbus_slave_ip_cb_pv = "172.168.200.3"
# Listening port
modbus_slave_port = 502
# Listening slave ID
modbus_slave_id = 255
# status list[address,type,length,default_value]
cb_status_addr = [12000, 'int16', 1, 5]
voltage_addr = [12029, 'int16', 1, 480]
active_power_addr = [12040, 'int16', 1, 0]
reactive_power_addr = [12044, 'int16', 1, 0]
rotation1_addr = [21190, 'int16', 1, 2]
rotation2_addr = [8871, 'int16', 1, 2]
# Control address
cb_cmd_addr = [7999]
# CB type
cb = {'NSX': 4353, 'MTZ2': 5377}
status = {4: 'Open', 5: 'Close'}


# ------------------------------------------------------------------------------

def cb_simulator(modbus_slave_ip, cb_type):
    # Connect to the log database
    conn = psycopg2.connect(dbname="microgrid", user="postgres", password="postgres", host="192.9.163.61", port="5432")
    cur = conn.cursor()
    # Create the server
    server = modbus_tcp.TcpServer(address=modbus_slave_ip, port=modbus_slave_port)
    # Start the server
    server.start()
    # Add slave
    slave_1 = server.add_slave(modbus_slave_id)
    # Add data blocks
    slave_1.add_block('A', cst.HOLDING_REGISTERS, 11999, 200)
    slave_1.add_block('B', cst.HOLDING_REGISTERS, 7999, 30)
    slave_1.add_block('C', cst.HOLDING_REGISTERS, 21190, 1)
    slave_1.add_block('D', cst.HOLDING_REGISTERS, 8871, 1)
    slave_1.set_values('A', cb_status_addr[0], cb_status_addr[3])
    slave_1.set_values('A', voltage_addr[0], voltage_addr[3])
    slave_1.set_values('A', active_power_addr[0], active_power_addr[3])
    slave_1.set_values('A', reactive_power_addr[0], reactive_power_addr[3])
    slave_1.set_values('C', rotation1_addr[0], rotation1_addr[3])
    slave_1.set_values('D', rotation2_addr[0], rotation2_addr[3])
    # Created a shared memory to exchange CB status and active power
    try:
        shm = shared_memory.SharedMemory(name=modbus_slave_ip, create=True, size=10)
    except BaseException:
        shm = shared_memory.SharedMemory(name=modbus_slave_ip, create=False, size=10)
    while True:
        # Read data from each Modbus register, convert it from machine code to int. These values are inputs of the simulator engine
        cb_status_c = slave_1.get_values('A', cb_status_addr[0], 1)
        cb_status_int = C2int(cb_status_addr[1], cb_status_c)
        cb_cmd_int = slave_1.get_values('B', cb_cmd_addr[0], 6)
        # if open command received, change CB status to open(0)
        if cb_cmd_int == (904, 10, cb[cb_type], 1, 13107, 13107):
            cb_status_int = 4
            print(modbus_slave_ip, 'Open command received:', datetime.datetime.now())
            cur.execute(
                "INSERT INTO Control values(DEFAULT,now(),'{}','control_command_received_{}')".format(modbus_slave_ip,
                                                                                                      cb_cmd_int[0]))
            conn.commit()
            # If correct control command received, reset control register
            slave_1.set_values('B', cb_cmd_addr[0], [0] * 6)
            print(modbus_slave_ip, 'Open command executed:', datetime.datetime.now())
        # if close command received, change CB status to closed(1)
        elif cb_cmd_int == (905, 10, cb[cb_type], 1, 13107, 13107):
            cb_status_int = 5
            print(modbus_slave_ip, 'Close command received', datetime.datetime.now())
            cur.execute(
                "INSERT INTO Control values(DEFAULT,now(),'{}','control_command_received_{}')".format(modbus_slave_ip,
                                                                                                      cb_cmd_int[0]))
            conn.commit()
            # If correct control command received, reset control register
            slave_1.set_values('B', cb_cmd_addr[0], [0] * 6)
            print(modbus_slave_ip, 'Close command executed', datetime.datetime.now())
        else:
            pass
        # Update new CB status to Modbus register
        slave_1.set_values('A', cb_status_addr[0], cb_status_int)
        # Save CB status to shared memory, data type is int8
        shm.buf[0] = cb_status_int
        # Read active power from shared memory, float32
        print('memory:',shm, shm.buf[1], shm.buf[2], shm.buf[3], shm.buf[4])
        active_power_c = [shm.buf[1] * 256 + shm.buf[2], shm.buf[3] * 256 + shm.buf[4]]
        # Convert active power from float32 to int
        active_power_int = C2int('float32', active_power_c)
        # Convert active power from int to C structure(int16)
        active_power_c = int2C(active_power_addr[1], active_power_int)
        # Update new CB status to Modbus register
        slave_1.set_values('A', active_power_addr[0], active_power_c)
        # Close the link to shared memory
        # timer for next cycle
        time.sleep(0.4)


if __name__ == "__main__":
    cb_simulator(modbus_slave_ip_cb_pv, 'MTZ2')
