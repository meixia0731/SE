import random
import struct
import time
import psycopg2
from multiprocessing import shared_memory
import modbus_tk.defines as cst
import modbus_tk.modbus_tcp as modbus_tcp

# --------------------------------------------------------------------
# Listening IP address
modbus_slave_ip_pv = '172.168.200.8'
modbus_slave_ip_cb_pv = "172.168.200.3"
# Listening port
modbus_slave_port = 502
# Listening slave ID
modbus_slave_id = 1
# --------------------------------------------------------------------
# data points configuration, [modbus_address, data_type, length, initial_value]
active_power_addr = [8069, 'uint64', 4, 0]
reactive_power_addr = [8075, 'int64', 4, 10000]
limitation_power_addr = [8085, 'uint32', 2, 30000]
start_stop_status_addr = [8067, 'uint16', 1, 1]
start_stop_cmd_addr = [8002, 'uint16', 1, 1]
active_power_sp_addr = [8005, 'uint32', 2, 30000]
energy_addr = [8079, 'uint64', 4, 30000]
# --------------------------------------------------------------------
# Scaling
p_scaling = 100
p_sp_scaling = 100
# --------------------------------------------------------------------
# Ramp_rate
Ramp_rate_percentage = 0.3
# --------------------------------------------------------------------
cmd_str = {0: 'Stop', 1: 'Start'}
status_str = {0: 'Stopped', 1: 'Started'}

# --------------------------------------------------------------------
def pv_simulator():
    start_stop_cmd_old = 0
    active_power_sp_old = 0
    # Connect to the log database
    conn = psycopg2.connect(dbname="microgrid", user="postgres",password="postgres", host="127.0.0.1", port="5432")
    cur = conn.cursor()

    # Create the server
    server = modbus_tcp.TcpServer(address=modbus_slave_ip_pv, port=modbus_slave_port)
    server.start()

    # Add slave
    slave_1 = server.add_slave(modbus_slave_id)

    # Add data blocks
    slave_1.add_block('A', cst.ANALOG_INPUTS, 8000, 150)
    slave_1.add_block('B', cst.HOLDING_REGISTERS, 8000, 10)

    # Initialization, convert data to C structure
    active_power_c = int2C(active_power_addr[1], active_power_addr[3])
    reactive_power_c = int2C(reactive_power_addr[1], reactive_power_addr[3])
    limitation_power_c = int2C(limitation_power_addr[1], limitation_power_addr[3])
    start_stop_status_c = int2C(start_stop_status_addr[1], start_stop_status_addr[3])
    start_stop_cmd_c = int2C(start_stop_cmd_addr[1], start_stop_cmd_addr[3])
    active_power_sp_c = int2C(active_power_sp_addr[1], active_power_sp_addr[3])
    energy_c = int2C(energy_addr[1], energy_addr[3])

    slave_1.set_values('A', active_power_addr[0], active_power_c)
    slave_1.set_values('A', reactive_power_addr[0], reactive_power_c)
    slave_1.set_values('A', limitation_power_addr[0], limitation_power_c)
    slave_1.set_values('A', start_stop_status_addr[0], start_stop_status_c)
    slave_1.set_values('B', start_stop_cmd_addr[0], start_stop_cmd_c)
    slave_1.set_values('B', active_power_sp_addr[0], active_power_sp_c)
    slave_1.set_values('A', energy_addr[0], energy_c)

    # Connect to the memory
    shm = shared_memory.SharedMemory(name=modbus_slave_ip_cb_pv, create=False, size=10)
    while True:
        print('--------------------------------')
        # Read data from slave memory, C structure
        active_power_c = slave_1.get_values('A', active_power_addr[0], active_power_addr[2])
        reactive_power_c = slave_1.get_values('A', reactive_power_addr[0], reactive_power_addr[2])
        limitation_power_c = slave_1.get_values('A', limitation_power_addr[0], limitation_power_addr[2])
        start_stop_status_c = slave_1.get_values('A', start_stop_status_addr[0], start_stop_status_addr[2])
        start_stop_cmd_c = slave_1.get_values('B', start_stop_cmd_addr[0], start_stop_cmd_addr[2])
        active_power_sp_c = slave_1.get_values('B', active_power_sp_addr[0], active_power_sp_addr[2])
        energy_c = slave_1.get_values('A', energy_addr[0], energy_addr[2])

        # Convert C structure to INT, as engine inputs
        active_power_int = C2int(active_power_addr[1], active_power_c)
        reactive_power_int = C2int(reactive_power_addr[1], reactive_power_c)
        limitation_power_int = C2int(limitation_power_addr[1], limitation_power_c)
        start_stop_status_int = C2int(start_stop_status_addr[1], start_stop_status_c)
        start_stop_cmd_int = C2int(start_stop_cmd_addr[1], start_stop_cmd_c)
        active_power_sp_int = C2int(active_power_sp_addr[1], active_power_sp_c)
        energy_int = C2int(energy_addr[1], energy_c)

        print('Engine Inputs:')
        print('active_power:', active_power_int, 'W')
        print('reactive_power:', reactive_power_int, 'Var')
        print('limitation_power:', limitation_power_int, 'W')
        print('start_stop_status:', status_str[start_stop_status_int])
        print('start_stop_cmd:', cmd_str[start_stop_cmd_int])
        print('active_power_setpoint:', active_power_sp_int, 'W')
        print('energy_int:', energy_int, 'Wh')
        # if new commands received, add them into log
        if start_stop_cmd_int != start_stop_cmd_old:
            cur.execute(
                "INSERT INTO sim_log values(DEFAULT,now(),'{}','start_stop_cmd_changed_from_{}_to_{}')".format(modbus_slave_ip,start_stop_cmd_old,start_stop_cmd_int))
            start_stop_cmd_old = start_stop_cmd_int
            conn.commit()
        if active_power_sp_int != active_power_sp_old:
            cur.execute(
                "INSERT INTO sim_log values(DEFAULT,now(),'{}','active_power_setpoint_changed_from_{}_to_{}')".format(modbus_slave_ip,active_power_sp_old,active_power_sp_int))
            active_power_sp_old = active_power_sp_int
            conn.commit()
        # if stop command received, change P setpoint to zero. New P = P + (P_setpint-P)*Ramprate
        if start_stop_cmd_int == 0:
            active_power_int = int(
                ((0 - active_power_int) * Ramp_rate_percentage + active_power_int) * random.uniform(0.98, 1.02))
        elif start_stop_cmd_int == 1:
            active_power_int = int(((min(active_power_sp_int,
                                         limitation_power_int) - active_power_int) * Ramp_rate_percentage + active_power_int) * random.uniform(
                0.99, 1.01))
        else:
            print('cmd input out of range, 0 for stop, 1 for start')
            active_power_int = int(((min(active_power_sp_int,
                                         limitation_power_int) - active_power_int) * Ramp_rate_percentage + active_power_int) * random.uniform(
                0.99, 1.01))
        active_power_c = int2C(active_power_addr[1], active_power_int)
        slave_1.set_values('A', active_power_addr[0], active_power_c)
        # if stop command received AND active_power = 0, change status to Stopped; else change status to Started
        if start_stop_cmd_int == 0 and active_power_int == 0:
            start_stop_status_int = 0
            start_stop_status_c = int2C(start_stop_status_addr[1], start_stop_status_int)
            slave_1.set_values('A', start_stop_status_addr[0], start_stop_status_c)
        else:
            start_stop_status_int = 1
            start_stop_status_c = int2C(start_stop_status_addr[1], start_stop_status_int)
            slave_1.set_values('A', start_stop_status_addr[0], start_stop_status_c)
        print('')
        print('Engine Outputs:')
        print('active_power:', active_power_int, 'W')
        print('start_stop_status:', status_str[start_stop_status_int])
        print('--------------------------------')
        time.sleep(2)
    cur.close()
    conn.close()


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
    pv_simulator()
