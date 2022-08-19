import time
import modbus_tk.defines as cst
import modbus_tk.modbus_tcp as modbus_tcp
import datetime
import psycopg2
import random
from multiprocessing import shared_memory
import struct

# --------------------------------------------------------------------
# Listening IP address
modbus_slave_ip_cb = '172.168.200.7'
modbus_slave_ip_cb_bess = '172.168.200.4'
# Listening port
modbus_slave_port = 502
# Listening slave ID
modbus_slave_id = 1
# --------------------------------------------------------------------
# data points configuration, [modbus_address, data_type, length, initial_value]
# Start_ctrl_addr = [8069, 'uint64', 4, 0]
# Stop_ctrl_addr = [8069, 'uint64', 4, 0]
# Power_setpoint = [8069, 'uint64', 4, 0]
# Measurements
Voltage_V12 = [71, 'float32', 2, 380]
Voltage_V23 = [73, 'float32', 2, 380]
Voltage_V31 = [75, 'float32', 2, 380]
Current_I1 = [79, 'float32', 2, 3]
Current_I2 = [81, 'float32', 2, 3]
Current_I3 = [83, 'float32', 2, 3]
Active_Power = [59, 'float32', 2, 100]
Reactive_Power = [61, 'float32', 2, -100]
Frequency = [65, 'float32', 2, 50]
SOC = [523, 'float32', 2, 50]
# Control commands
Start_cmd = [2100, 'uint16', 1, 1]
Stop_cmd = [2101, 'uint16', 1, 0]
Alarm_rst_cmd = [2102, 'uint16', 1, 0]
Auto_mode_cmd = [2103, 'uint16', 1, 0]
Operator_mode_cmd = [2104, 'uint16', 1, 1]
P_enable_cmd = [2105, 'uint16', 1, 1]
P_disable_cmd = [2106, 'uint16', 1, 0]
# Active power setpoint
SP_cmd = [2151, 'float32', 2, -30]
SP_cmd_f = [2337, 'float32', 2, -30]

# Status
Running = 1
Starting = 0
Stopping = 0
Stopped = 0
Online = 1
Auto_Mode_Active = 0
Manual_Mode_Active = 0
Operator_Mode_Active = 1
AC_CB_Closed = 0
Alarms_Healthy = 1
Grid_Tie_CB_closed = 0
Upstream_Customer_CB_Closed = 0
Dead_powerstore_AC_connection_status = 0
Grid_Ready_Status = 0
Grid_Healthy_Status = 0
Dead_microgrid_status = 0
Reg_4_int = Alarms_Healthy * 512 + AC_CB_Closed * 256 + Operator_Mode_Active * 128 + Manual_Mode_Active * 64 + Auto_Mode_Active * 32 + Online * 16 + Stopped * 8 + Stopping * 4 + Starting * 2 + Running
Reg_4 = [4, 'uint16', 1, Reg_4_int]
Reg_5 = [5, 'uint16', 1, 4096]

Max_charge_power = [185, 'float32', 2, 300]
Max_discharge_power = [187, 'float32', 2, 300]
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
    # Link to the shared memory to talk with BESS CB
    # Create the server
    server = modbus_tcp.TcpServer(address=modbus_slave_ip_cb, port=modbus_slave_port)
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
    # Status initialization
    Reg_4_c = int2C(Reg_4[1], Reg_4[3])
    slave_1.set_values('A', Reg_4[0], Reg_4_c)
    Reg_5_c = int2C(Reg_5[1], Reg_5[3])
    slave_1.set_values('A', Reg_5[0], Reg_5_c)
    # Status initialization
    Max_charge_power_c = int2C(Max_charge_power[1], Max_charge_power[3])
    slave_1.set_values('A', Max_charge_power[0], Max_charge_power_c)
    Max_discharge_power_c = int2C(Max_discharge_power[1], Max_discharge_power[3])
    slave_1.set_values('A', Max_discharge_power[0], Max_discharge_power_c)
    while True:
        try:
            shm = shared_memory.SharedMemory(name=modbus_slave_ip_cb_bess, create=True, size=10)
        except BaseException:
            shm = shared_memory.SharedMemory(name=modbus_slave_ip_cb_bess, create=False, size=10)
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
        # Read status from slave memory, C structure
        Reg_4_c = slave_1.get_values('A', Reg_4[0], Reg_4[2])
        Reg_4_int = C2int(Reg_4[1], Reg_4_c)
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
        # if CB open, stop calculation
        cb_status = shm.buf[0]
        if cb_status == 4:
            Active_Power_int = 0
        # else start the calculation
        else:
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
        # send P to CB
        print('Active_Power_int is :',Active_Power_int)
        if Active_Power_int >= 0:
            shm.buf[1] = 1
            shm.buf[2] = int(Active_Power_int) // 255
            shm.buf[3] = int(Active_Power_int) % 255
        elif Active_Power_int < 0:
            shm.buf[1] = 2
            shm.buf[2] = ((-1)*int(Active_Power_int)) // 255
            shm.buf[3] = ((-1)*int(Active_Power_int)) % 255
        print('shm is :',shm.buf[1],shm.buf[2],shm.buf[3])
        shm.close()
        SP_cmd_f_c = int2C(SP_cmd_f[1], SP_cmd_int)
        slave_1.set_values('A', SP_cmd_f[0], SP_cmd_f_c)
        print(list(map(int,list(bin(Reg_4_int))[2:])))
        Reg_4_value = list(map(int, list(bin(Reg_4_int))[2:]))
        Reg_4_value.reverse()
        print(Reg_4_value)
        (Running, Starting, Stopping, Stopped, Online, Auto_Mode_Active, Manual_Mode_Active, Operator_Mode_Active,
         AC_CB_Closed, Alarms_Healthy) = Reg_4_value
        if Start_cmd_int == 1 and Stop_cmd_int == 0:
            Running = 1
            Stopped = 0
            Online = 1
        elif Start_cmd_int == 0 and Stop_cmd_int == 1:
            Running = 0
            Stopped = 1
            Online = 0

        if Operator_mode_cmd_int == 1:
            Operator_Mode_Active = 1
        else:
            Operator_Mode_Active = 0
        Reg_4_int = Alarms_Healthy * 512 + AC_CB_Closed * 256 + Operator_Mode_Active * 128 + Manual_Mode_Active * 64 + Auto_Mode_Active * 32 + Online * 16 + Stopped * 8 + Stopping * 4 + Starting * 2 + Running
        Reg_4_c = int2C(Reg_4[1], Reg_4_int)
        slave_1.set_values('A', Reg_4[0], Reg_4_c)

        if P_enable_cmd_int == 1:
            Reg_5_c = int2C(Reg_5[1], 4096)
            slave_1.set_values('A', Reg_5[0], Reg_5_c)
        else:
            Reg_5_c = int2C(Reg_5[1], 0)
            slave_1.set_values('A', Reg_5[0], Reg_5_c)
        print('Running:', Running)
        print('Stopped:', Stopped)
        print('Online:', Online)
        print('Operator_Mode_Active:', Operator_Mode_Active)

        if Active_Power_int == 0:
            Current_I1_int = 0
        else:
            Current_I1_int = 1.732 * Active_Power_int / (3 * Voltage_V12_int)
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
        return [struct.unpack('>H', value[2:4])[0], struct.unpack('>H', value[0:2])[0]]
    elif data_type == 'float64':
        value = struct.pack('>d', value)
        return [struct.unpack('>H', value[0:2])[0], struct.unpack('>H', value[2:4])[0],
                struct.unpack('>H', value[4:6])[0], struct.unpack('>H', value[6:8])[0]]
    else:
        print("Input is not defined")
        return


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
            bytes_value = struct.pack('>H', i) + bytes_value
        return struct.unpack('>f', bytes_value)[0]
    elif data_type == 'float64':
        for i in value:
            bytes_value = bytes_value + struct.pack('>H', i)
        return struct.unpack('>d', bytes_value)[0]
    else:
        print("Input is not defined")
        return


if __name__ == "__main__":
    bess_simulator()
