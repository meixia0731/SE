import time
import modbus_tk.defines as cst
import modbus_tk.modbus_tcp as modbus_tcp
import datetime
import psycopg2
import random
from multiprocessing import shared_memory
import struct

# ------------------------------------------------------------------------------

# Configuration:

# Listening IP address
modbus_slave_ip_cb_utility = "172.168.200.1"
modbus_slave_ip_cb_load = "172.168.200.2"
modbus_slave_ip_cb_bess = "172.168.200.4"
modbus_slave_ip_cb_pv = "172.168.200.3"
# Listening port
modbus_slave_port = 502
# Listening slave ID
modbus_slave_id = 255
# list[address,length,sign,default_value]
CB_Status_addr = [12000, 16, 2, 5]
CB_Cmd_addr = [7999]
Voltage_addr = [12029,230]
P_addr = [12040,100]
Q_addr = [12044,2]
# CB type
CB = {'NSX': 4353, 'MTZ2': 5377}
Status = {4: 'Open', 5: 'Close'}

# ------------------------------------------------------------------------------

def CB_SIMULATOR(modbus_slave_ip, cb_type):
    # Connect to the log database
    conn = psycopg2.connect(dbname="microgrid", user="postgres",password="postgres", host="172.168.200.1", port="5432")
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
    while True:
        try:
            shm_load = shared_memory.SharedMemory(name=modbus_slave_ip_cb_load, create=True, size=10)
            shm_pv = shared_memory.SharedMemory(name=modbus_slave_ip_cb_pv, create=True, size=10)
            shm_bess = shared_memory.SharedMemory(name=modbus_slave_ip_cb_bess, create=True, size=10)
        except BaseException:
            shm_load = shared_memory.SharedMemory(name=modbus_slave_ip_cb_load, create=False, size=10)
            shm_pv = shared_memory.SharedMemory(name=modbus_slave_ip_cb_pv, create=False, size=10)
            shm_bess = shared_memory.SharedMemory(name=modbus_slave_ip_cb_bess, create=False, size=10)
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
        if cb_status_int[0] == 4:
            slave_1.set_values('A', P_addr[0], 0)
            slave_1.set_values('A', Q_addr[0], 0)
        elif cb_status_int[0] == 5:
            if shm_load.buf[1] == 1:
                load_p = shm_load.buf[2]*255 + shm_load.buf[3]
            else:
                load_p = (shm_load.buf[2]*255 + shm_load.buf[3])*(-1)
            if shm_pv.buf[1] == 1:
                pv_p = shm_pv.buf[2]*255 + shm_pv.buf[3]
            else:
                pv_p = (shm_pv.buf[2]*255 + shm_pv.buf[3])*(-1)
            if shm_bess.buf[1] == 1:
                bess_p = shm_bess.buf[2]*255 + shm_bess.buf[3]
            else:
                bess_p = (shm_bess.buf[2]*255 + shm_bess.buf[3])*(-1)
            utility_p = load_p - pv_p - bess_p
        Active_Power_c = int2C('int16', int(utility_p*10))
        slave_1.set_values('A', P_addr[0], Active_Power_c)
        slave_1.set_values('A', CB_Status_addr[0], cb_status_int)
        slave_1.set_values('A', Voltage_addr[0], Voltage_addr[1])
        shm_load.close()
        shm_pv.close()
        shm_bess.close()
        time.sleep(0.4)
def int2C(data_type, value, endianness='big'):
    if data_type == 'uint64':
        value = struct.pack('>Q', value)
        return [struct.unpack('>H', value[0:2])[0], struct.unpack('>H', value[2:4])[0],
                struct.unpack('>H', value[4:6])[0], struct.unpack('>H', value[6:8])[0]]
    elif data_type == 'int64':
        value = struct.pack('>q', value)
        return [struct.unpack('>H', value[0:2])[0], struct.unpack('>H', value[2:4])[0],
                struct.unpack('>H', value[4:6])[0], struct.unpack('>H', value[6:8])[0]]
    elif data_type == 'uint32':
        value = struct.pack('>L', value)
        return [struct.unpack('>H', value[0:2])[0], struct.unpack('>H', value[2:4])[0]]
    elif data_type == 'int32':
        value = struct.pack('>l', value)
        return [struct.unpack('>H', value[0:2])[0], struct.unpack('>H', value[2:4])[0]]
    elif data_type == 'uint16':
        value = struct.pack('>H', value)
        return [struct.unpack('>H', value[0:2])[0]]
    elif data_type == 'int16':
        value = struct.pack('>h', value)
        return [struct.unpack('>H', value[0:2])[0]]
    elif data_type == 'float16':
        value = struct.pack('>e', value)
        return [struct.unpack('>H', value[0:2])[0]]
    elif data_type == 'float32':
        value = struct.pack('>f', value)
        return [struct.unpack('>H', value[0:2])[0], struct.unpack('>H', value[2:4])[0]]
    if data_type == 'float64':
        value = struct.pack('>d', value)
        return [struct.unpack('>H', value[0:2])[0], struct.unpack('>H', value[2:4])[0],
                struct.unpack('>H', value[4:6])[0], struct.unpack('>H', value[6:8])[0]]

def C2int(data_type, value, endianness='big'):
    bytes_value = b''
    if data_type == 'uint64':
        for i in value:
            bytes_value = bytes_value + struct.pack('>H', i)
        return struct.unpack('>Q', bytes_value)[0]
    elif data_type == 'int64':
        for i in value:
            bytes_value = bytes_value + struct.pack('>H', i)
        return struct.unpack('>q', bytes_value)[0]
    elif data_type == 'uint32':
        for i in value:
            bytes_value = bytes_value + struct.pack('>H', i)
        return struct.unpack('>L', bytes_value)[0]
    elif data_type == 'int32':
        for i in value:
            bytes_value = bytes_value + struct.pack('>H', i)
        return struct.unpack('>l', bytes_value)[0]
    elif data_type == 'uint16':
        for i in value:
            bytes_value = struct.pack('>H', i)
        return struct.unpack('>H', bytes_value)[0]
    elif data_type == 'int16':
        for i in value:
            bytes_value = struct.pack('>H', i)
        return struct.unpack('>h', bytes_value)[0]
    elif data_type == 'float16':
        for i in value:
            bytes_value = struct.pack('>H', i)
        return struct.unpack('>e', bytes_value)[0]
    elif data_type == 'float32':
        for i in value:
            bytes_value = bytes_value + struct.pack('>H', i)
        return struct.unpack('>f', bytes_value)[0]
    elif data_type == 'float64':
        for i in value:
            bytes_value = bytes_value + struct.pack('>H', i)
        return struct.unpack('>d', bytes_value)[0]


if __name__ == "__main__":
    CB_SIMULATOR(modbus_slave_ip_cb_utility,'MTZ2')
