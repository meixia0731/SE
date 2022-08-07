import random
import struct
import time

import modbus_tk.defines as cst
import modbus_tk.modbus_tcp as modbus_tcp

# --------------------------------------------------------------------
# Listening IP address
modbus_slave_ip = '0.0.0.0'
# Listening port
modbus_slave_port = 502
# Listening slave ID
modbus_slave_id = 1
# --------------------------------------------------------------------
# data points configuration, [modbus_address, data_type, length, initial_value]
Start_ctrl_addr = [8069, 'uint64', 4, 0]
Stop_ctrl_addr = [8069, 'uint64', 4, 0]
Power_setpoint = [8069, 'uint64', 4, 0]

# --------------------------------------------------------------------
# Scaling
p_scaling = 100
p_sp_scaling = 100
# --------------------------------------------------------------------
# Ramp_rate
Ramp_rate_percentage = 0.3
# --------------------------------------------------------------------

# --------------------------------------------------------------------
def bess_simulator():
    # Create the server
    server = modbus_tcp.TcpServer(address=modbus_slave_ip, port=modbus_slave_port)
    server.start()

    # Add slave
    slave_1 = server.add_slave(modbus_slave_id)

    # Add data blocks
    slave_1.add_block('A', cst.ANALOG_INPUTS, 8000, 150)
    slave_1.add_block('B', cst.HOLDING_REGISTERS, 8000, 10)

    # Initialization, convert data to C structure
    active_power_c = int2C(active_power_addr[1], active_power_addr[3])
    slave_1.set_values('A', active_power_addr[0], active_power_c)


    # Read setpoint and generate feedback
    while True:
        print('--------------------------------')
        # Read data from slave memory, C structure
        active_power_c = slave_1.get_values('A', active_power_addr[0], active_power_addr[2])
        # Convert C structure to INT, as engine inputs
        active_power_int = C2int(active_power_addr[1], active_power_c)
        print('Engine Inputs:')
        print('active_power:', active_power_int, 'W')
        time.sleep(1)


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
    bess_simulator()
