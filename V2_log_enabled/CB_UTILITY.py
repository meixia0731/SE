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
modbus_slave_ip_cb_utility = "172.168.200.1"
modbus_slave_ip_cb_load = "172.168.200.2"
modbus_slave_ip_cb_chp = "172.168.200.5"
modbus_slave_ip_cb_pv = "172.168.200.3"
modbus_slave_ip_cb_bess = '172.168.200.4'

scaling_cb = -1
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
        shm_cb_utility = shared_memory.SharedMemory(name=modbus_slave_ip_cb_utility, create=True, size=10)
    except BaseException:
        shm_cb_utility = shared_memory.SharedMemory(name=modbus_slave_ip_cb_utility, create=False, size=10)
    try:
        shm_cb_chp = shared_memory.SharedMemory(name=modbus_slave_ip_cb_chp, create=True, size=10)
    except BaseException:
        shm_cb_chp = shared_memory.SharedMemory(name=modbus_slave_ip_cb_chp, create=False, size=10)
    try:
        shm_cb_pv = shared_memory.SharedMemory(name=modbus_slave_ip_cb_pv, create=True, size=10)
    except BaseException:
        shm_cb_pv = shared_memory.SharedMemory(name=modbus_slave_ip_cb_pv, create=False, size=10)
    try:
        shm_cb_bess = shared_memory.SharedMemory(name=modbus_slave_ip_cb_bess, create=True, size=10)
    except BaseException:
        shm_cb_bess = shared_memory.SharedMemory(name=modbus_slave_ip_cb_bess, create=False, size=10)
    try:
        shm_cb_load = shared_memory.SharedMemory(name=modbus_slave_ip_cb_load, create=True, size=10)
    except BaseException:
        shm_cb_load = shared_memory.SharedMemory(name=modbus_slave_ip_cb_load, create=False, size=10)
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
        shm_cb_utility.buf[0] = cb_status_int
        if cb_status_int == 4:
            active_power_utility_int = 0
        else:
            active_power_load_c = [shm_cb_load.buf[1] * 256 + shm_cb_load.buf[2], shm_cb_load.buf[3] * 256 + shm_cb_load.buf[4]]
            active_power_load_int = C2int('float32', active_power_load_c)
            active_power_chp_c = [shm_cb_chp.buf[1] * 256 + shm_cb_chp.buf[2], shm_cb_chp.buf[3] * 256 + shm_cb_chp.buf[4]]
            active_power_chp_int = C2int('float32', active_power_chp_c)
            active_power_pv_c = [shm_cb_pv.buf[1] * 256 + shm_cb_pv.buf[2], shm_cb_pv.buf[3] * 256 + shm_cb_pv.buf[4]]
            active_power_pv_int = C2int('float32', active_power_pv_c)
            active_power_bess_c = [shm_cb_bess.buf[1] * 256 + shm_cb_bess.buf[2], shm_cb_bess.buf[3] * 256 + shm_cb_bess.buf[4]]
            active_power_bess_int = C2int('float32', active_power_bess_c)
            print(active_power_load_int)
            print(active_power_chp_int)
            print(active_power_pv_int)
            print(active_power_bess_int)
            active_power_utility_int = scaling_cb*(active_power_load_int + active_power_chp_int + active_power_pv_int + active_power_bess_int)
        active_power_c = int2C(active_power_addr[1], active_power_utility_int)
        # Update new CB status to Modbus register
        slave_1.set_values('A', active_power_addr[0], active_power_c)

        active_power_memory = int2C('float32', active_power_utility_int)
        shm_cb_utility.buf[1] = active_power_memory[0] // 256
        shm_cb_utility.buf[2] = active_power_memory[0] % 256
        shm_cb_utility.buf[3] = active_power_memory[1] // 256
        shm_cb_utility.buf[4] = active_power_memory[1] % 256

        time.sleep(0.4)


if __name__ == "__main__":
    cb_simulator(modbus_slave_ip_cb_utility, 'MTZ2')
