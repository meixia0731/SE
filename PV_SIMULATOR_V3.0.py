import random
import struct
import time

import modbus_tk.defines as cst
import modbus_tk.modbus_tcp as modbus_tcp

# --------------------------------------------------------------------t
modbus_slave_ip = '0.0.0.0'
# Listening port
modbus_slave_port = 502

# Listening slave ID
modbus_slave_id = 1

active_power_scaling = 1
active_power_sp_scaling = 1

# list[address,length,sign,default_value]
active_power_addr = [8069, 'int64', 1]
reactive_power_addr = [8075, 'int64', 10000]
limitation_power_addr = [8085, 32, 2, 30000]
start_stop_status_addr = [8067, 16, 2, 21]
start_stop_cmd_addr = [8002, 16, 2, 1]
active_power_sp_addr = [8005, 32, 2, 30000]
energy_addr = [8079, 64, 2, 0]

# Ramp_rate: 1 means percentage, 2 means kw
Ramp_rate_type = 1
Ramp_rate_value = 5
Ramp_rate_percentage = 0.3


# ------------------------------------------------------------------------------

def pv_simulator():
    # Create the server
    server = modbus_tcp.TcpServer(address=modbus_slave_ip, port=modbus_slave_port)
    server.start()

    # Add slave
    slave_1 = server.add_slave(modbus_slave_id)

    # Add data blocks
    slave_1.add_block('A', cst.ANALOG_INPUTS, 8000, 150)
    slave_1.add_block('B', cst.HOLDING_REGISTERS, 8000, 10)

    # Initialization, convert data to machine code
    active_power_c = int2C(active_power_addr[1], active_power_addr[2])
    slave_1.set_values('A', active_power_addr[0], active_power_c)

    # Read setpoint and generate feedback
    while True:
        # Read data from memory, convert it from machine code to int. These values are input of the simulator engine
        active_power_c = slave_1.get_values('A', active_power_addr[0], 4)
        print('read:active_power_c',active_power_c)
        active_power_int = C2int(active_power_addr[1], active_power_c)
        print('decode:active_power_int',active_power_int)
        active_power_int = random.randint(-9223372036854775807,9223372036854775807)
        print('new:active_power_int',active_power_int)
        active_power_c = int2C(active_power_addr[1], active_power_int)
        print('send:active_power_c',active_power_c)
        slave_1.set_values('A', active_power_addr[0], active_power_c)

        time.sleep(2)
        print('--------------------------------')
        # if stop command received, change P setpoint to zero. New P = P + (P_setpint-P)*Ramprate


#       if Start_Stop_Cmd_INT == 0:
#           Active_Power_INT =  int(((0 - Active_Power_INT)*Ramp_rate_percentage + Active_Power_INT)*random.uniform(0.98,1.02)/active_power_scaling)
#       else:
#           Active_Power_INT =  int(((min(Active_Power_SP_INT,Limitation_Power_INT) - Active_Power_INT)*Ramp_rate_percentage + Active_Power_INT)*random.uniform(0.99,1.01)/active_power_scaling)

# Converter P to machine code
#       Active_Power_MC = Converter(Active_Power_INT,active_power_addr[1],1,active_power_addr[2])
# Update P to memory
#       slave_1.set_values('A', active_power_addr[0], Active_Power_MC)
#       print('Sent out Active_Power is', Active_Power_INT, 'kW','Scaling:',active_power_scaling)

def int2C(data_type, value):
    if data_type == 'uint64':
        value = struct.pack('>Q', value)
        return [struct.unpack('>H',value[0:2])[0], struct.unpack('>H',value[2:4])[0], struct.unpack('>H',value[4:6])[0], struct.unpack('>H',value[6:8])[0]]
    if data_type == 'int64':
        value = struct.pack('>q', value)
        return [struct.unpack('>H',value[0:2])[0], struct.unpack('>H',value[2:4])[0], struct.unpack('>H',value[4:6])[0], struct.unpack('>H',value[6:8])[0]]
def C2int(data_type, value):
    bytes_value = b''
    if data_type == 'uint64':
        for i in value:
            bytes_value = bytes_value + struct.pack('>H',i)
#        print('C2int output', struct.unpack('>Q',bytes_value))
        return struct.unpack('>Q',bytes_value)[0]
    if data_type == 'int64':
        for i in value:
            bytes_value = bytes_value + struct.pack('>H', i)
        #        print('C2int output', struct.unpack('>Q',bytes_value))
        return struct.unpack('>q', bytes_value)[0]

if __name__ == "__main__":
    pv_simulator()
