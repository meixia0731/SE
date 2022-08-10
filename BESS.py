import random
import struct
import time

import modbus_tk.defines as cst
import modbus_tk.modbus_tcp as modbus_tcp

# --------------------------------------------------------------------
# Listening IP address
modbus_slave_ip = '172.168.200.7'
# Listening port
modbus_slave_port = 502
# Listening slave ID
modbus_slave_id = 1
# --------------------------------------------------------------------
# data points configuration, [modbus_address, data_type, length, initial_value]
# Start_ctrl_addr = [8069, 'uint64', 4, 0]
# Stop_ctrl_addr = [8069, 'uint64', 4, 0]
# Power_setpoint = [8069, 'uint64', 4, 0]
Voltage_V12 = [71, 'float32', 2, 380]
Voltage_V23 = [73, 'float32', 2, 380]
Voltage_V31 = [75, 'float32', 2, 380]
Current_I1 = [79, 'float32', 2, 3]
Current_I2 = [81, 'float32', 2, 3]
Current_I3 = [83, 'float32', 2, 3]
Active_Power = [59, 'float32', 2, 0]
Reactive_Power = [61, 'float32', 2, 0]
Frequency = [65, 'float32', 2, 50]
SOC = [213, 'float32', 2, 50]

Start_cmd = [2100, 'int16', 1, 1]
Stop_cmd = [2101, 'int16', 1, 0]
Alarm_rst_cmd = [2102, 'int16', 1, 0]
Auto_mode_cmd = [2103, 'int16', 1, 0]
Operator_mode_cmd = [2104, 'int16', 1, 1]
P_enable_cmd = [2105, 'int16', 1, 1]
P_disable_cmd = [2106, 'int16', 1, 0]

SP_cmd = [2131, 'float32', 2, -300]
# Status_1
# Start_Status
# Starting_Status
# Stopping_Status
# Stop_Status
# Online_Status
# Auto_Mode
# Manual_Mode
# Operator_Mode
# AC_BC_Closed
# Healthy
# Status_2
# CTR_Active
# Heartbeat

# Apparent_Power

# Voltage_average

# Current_average
# Max_Charge_Power
# Max_Discharge_Power

# Alarm_Status
# Smoke_Alarm
# SCADA_Lost_Comms_Al
# PAct_01
# Start_Command_Feedback
# Stop_Command_Feedback
# Alarm_Reset_Command_Feedback
# Auto_Command_Feedback
# Operator_Command_Feedback
# Enable_Power_Control_Cmd_Feedback
# Disable_Power_Control_Cmd_Feedback
# Active_Power_Setpoint_Feedback

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
    slave_1.add_block('A', cst.HOLDING_REGISTERS, 1, 4000)
    slave_1.add_block('B', cst.COILS, 1, 4000)
    # Voltage initialization
    Voltage_V12_c = int2C(Voltage_V12[1], Voltage_V12[3])
    slave_1.set_values('A', Voltage_V12[0], Voltage_V12_c)
    Voltage_V23_c = int2C(Voltage_V23[1], Voltage_V23[3])
    slave_1.set_values('A', Voltage_V23[0], Voltage_V23_c)
    Voltage_V31_c = int2C(Voltage_V31[1], Voltage_V31[3])
    slave_1.set_values('A', Voltage_V31[0], Voltage_V31_c)
    # Current initialization
    Current_I1_c = int2C(Current_I1[1], Current_I1[3])
    slave_1.set_values('A', Current_I1[0], Current_I1_c)
    Current_I2_c = int2C(Current_I2[1], Current_I2[3])
    slave_1.set_values('A', Current_I2[0], Current_I2_c)
    Current_I3_c = int2C(Current_I3[1], Current_I3[3])
    slave_1.set_values('A', Current_I3[0], Current_I3_c)
    # P\Q\F initialization
    Active_Power_c = int2C(Active_Power[1], Active_Power[3])
    slave_1.set_values('A', Active_Power[0], Active_Power_c)
    Reactive_Power_c = int2C(Reactive_Power[1], Reactive_Power[3])
    slave_1.set_values('A', Reactive_Power[0], Reactive_Power_c)
    Frequency_c = int2C(Frequency[1], Frequency[3])
    slave_1.set_values('A', Frequency[0], Frequency_c)
    # SOC initialization
    SOC_c = int2C(SOC[1], SOC[3])
    slave_1.set_values('A', SOC[0], SOC_c)
    # SP_cmd initialization
    SP_cmd_c = int2C(SP_cmd[1], SP_cmd[3])
    slave_1.set_values('A', SP_cmd[0], SP_cmd_c)

    # Control initialization
    Start_cmd_c = int2C(Start_cmd[1], Start_cmd[3])
    slave_1.set_values('B', Start_cmd[0], Start_cmd_c)
    Stop_cmd_c = int2C(Stop_cmd[1], Stop_cmd[3])
    slave_1.set_values('B', Stop_cmd[0], Stop_cmd_c)
    Alarm_rst_cmd_c = int2C(Alarm_rst_cmd[1], Alarm_rst_cmd[3])
    slave_1.set_values('B', Alarm_rst_cmd[0], Alarm_rst_cmd_c)
    Auto_mode_cmd_c = int2C(Auto_mode_cmd[1], Auto_mode_cmd[3])
    slave_1.set_values('B', Auto_mode_cmd[0], Auto_mode_cmd_c)
    Operator_mode_cmd_c = int2C(Operator_mode_cmd[1], Operator_mode_cmd[3])
    slave_1.set_values('B', Operator_mode_cmd[0], Operator_mode_cmd_c)
    P_enable_cmd_c = int2C(P_enable_cmd[1], P_enable_cmd[3])
    slave_1.set_values('B', P_enable_cmd[0], P_enable_cmd_c)
    P_disable_cmd_c = int2C(P_disable_cmd[1], P_disable_cmd[3])
    slave_1.set_values('B', P_disable_cmd[0], P_disable_cmd_c)
    # Read setpoint and generate feedback
    while True:
        print('--------------------------------')
        # Read voltage from slave memory, C structure
        Voltage_V12_c = slave_1.get_values('A', Voltage_V12[0], Voltage_V12[2])
        Voltage_V12_int = C2int(Voltage_V12[1], Voltage_V12_c)
        Voltage_V23_c = slave_1.get_values('A', Voltage_V23[0], Voltage_V23[2])
        Voltage_V23_int = C2int(Voltage_V23[1], Voltage_V23_c)
        Voltage_V31_c = slave_1.get_values('A', Voltage_V31[0], Voltage_V31[2])
        Voltage_V31_int = C2int(Voltage_V31[1], Voltage_V31_c)
        # Read current from slave memory, C structure
        Current_I1_c = slave_1.get_values('A', Current_I1[0], Current_I1[2])
        Current_I1_int = C2int(Current_I1[1], Current_I1_c)
        Current_I2_c = slave_1.get_values('A', Current_I2[0], Current_I2[2])
        Current_I2_int = C2int(Current_I2[1], Current_I2_c)
        Current_I3_c = slave_1.get_values('A', Current_I3[0], Current_I3[2])
        Current_I3_int = C2int(Current_I3[1], Current_I3_c)
        # Read P\Q\F from slave memory, C structure
        Active_Power_c = slave_1.get_values('A', Active_Power[0], Active_Power[2])
        Active_Power_int = C2int(Active_Power[1], Active_Power_c)
        Reactive_Power_c = slave_1.get_values('A', Reactive_Power[0], Reactive_Power[2])
        Reactive_Power_int = C2int(Reactive_Power[1], Reactive_Power_c)
        Frequency_c = slave_1.get_values('A', Frequency[0], Frequency[2])
        Frequency_int = C2int(Frequency[1], Frequency_c)
        # Read SOC from slave memory, C structure
        SOC_c = slave_1.get_values('A', SOC[0], SOC[2])
        SOC_int = C2int(SOC[1], SOC_c)
        # Read SP_cmd from slave memory, C structure
        SP_cmd_c = slave_1.get_values('A', SP_cmd[0], SP_cmd[2])
        SP_cmd_int = C2int(SP_cmd[1], SP_cmd_c)
        # Read Control from slave memory, C structure
        Start_cmd_c = slave_1.get_values('B', Start_cmd[0], Start_cmd[2])
        Start_cmd_int = C2int(Start_cmd[1], Start_cmd_c)
        Stop_cmd_c = slave_1.get_values('B', Stop_cmd[0], Stop_cmd[2])
        Stop_cmd_int = C2int(Stop_cmd[1], Stop_cmd_c)
        Alarm_rst_cmd_c = slave_1.get_values('B', Alarm_rst_cmd[0], Alarm_rst_cmd[2])
        Alarm_rst_cmd_int = C2int(Alarm_rst_cmd[1], Alarm_rst_cmd_c)
        Auto_mode_cmd_c = slave_1.get_values('B', Auto_mode_cmd[0], Auto_mode_cmd[2])
        Auto_mode_cmd_int = C2int(Auto_mode_cmd[1], Auto_mode_cmd_c)
        Operator_mode_cmd_c = slave_1.get_values('B', Operator_mode_cmd[0], Operator_mode_cmd[2])
        Operator_mode_cmd_int = C2int(Operator_mode_cmd[1], Operator_mode_cmd_c)
        P_enable_cmd_c = slave_1.get_values('B', P_enable_cmd[0], P_enable_cmd[2])
        P_enable_cmd_int = C2int(P_enable_cmd[1], P_enable_cmd_c)
        P_disable_cmd_c = slave_1.get_values('B', P_disable_cmd[0], P_disable_cmd[2])
        P_disable_cmd_int = C2int(P_disable_cmd[1], P_disable_cmd_c)
        print('Status update:')
        print('Voltage_V12:', Voltage_V12_int, 'VAC')
        print('Voltage_V23:', Voltage_V23_int, 'VAC')
        print('Voltage_V31:', Voltage_V31_int, 'VAC')
        print('Current_I1:', Current_I1_int, 'A')
        print('Current_I2:', Current_I2_int, 'A')
        print('Current_I3:', Current_I3_int, 'A')
        print('Active_Power:', Active_Power_int, 'kW')
        print('Reactive_Power:', Reactive_Power_int, 'kVAR')
        print('Frequency:', Frequency_int, 'Hz')
        print('SOC:', SOC_int, '%')
        print('SP_cmd:', SP_cmd_int, 'kW')
        print('Start_cmd:', Start_cmd_int)
        print('Stop_cmd:', Stop_cmd_int)
        print('Alarm_rst_cmd:', Alarm_rst_cmd_int)
        print('Auto_mode_cmd:', Auto_mode_cmd_int)
        print('Operator_mode_cmd:', Operator_mode_cmd_int)
        print('P_enable_cmd:', P_enable_cmd_int)
        print('P_disable_cmd:', P_disable_cmd_int)
        if Start_cmd_int > 0 and Operator_mode_cmd_int > 0 and P_enable_cmd_int > 0:
            SP_cmd_int = SP_cmd_int
        else:
            SP_cmd_int = random.randrange(-300,300)
        if (SOC_int > 0 and SOC_int < 100):
            SOC_int = SOC_int - (SP_cmd_int / 300)
            Active_Power_int = SP_cmd_int
        elif SOC_int <= 0:
            if SP_cmd_int < 0:
                SOC_int = SOC_int - (SP_cmd_int / 300)
            else:
                SOC_int = 0
                Active_Power_int = 0
        elif SOC_int >= 100:
            if SP_cmd_int > 0:
                SOC_int = SOC_int - (SP_cmd_int / 300)
            else:
                SOC_int = 100
                Active_Power_int = 0

        SOC_c = int2C(SOC[1], SOC_int)
        slave_1.set_values('A', SOC[0], SOC_c)
        Active_Power_c = int2C(Active_Power[1], Active_Power_int)
        slave_1.set_values('A', Active_Power[0], Active_Power_c)
        if Active_Power_int == 0:
            Current_I1_int = 0
        else:
            Current_I1_int = 1.732*Active_Power_int / (3 * Voltage_V12_int)
        Current_I1_c = int2C(SOC[1], Current_I1_int)
        slave_1.set_values('A', Current_I1[0], Current_I1_c)
        slave_1.set_values('A', Current_I2[0], Current_I1_c)
        slave_1.set_values('A', Current_I3[0], Current_I1_c)
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
