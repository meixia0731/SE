import time
import modbus_tk.defines as cst
import modbus_tk.modbus_tcp as modbus_tcp
import psycopg2
from multiprocessing import shared_memory
from data_type_converter import int2C as int2C
from data_type_converter import C2int as C2int

# --------------------------------------------------------------------
# Listening IP address
modbus_slave_ip_bess = '172.168.200.7'
modbus_slave_ip_cb_bess = '172.168.200.4'
scaling_cb = -10
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
SP_cmd = [2151, 'float32', 2, 30]
SP_cmd_f = [2337, 'float32', 2, -30]
# Energy
energy = [89, 'float32', 2, 33]
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

Max_charge_power = [185, 'float32', 2, 200]
Max_discharge_power = [187, 'float32', 2, 300]
# --------------------------------------------------------------------
# Scaling
p_scaling = 100
p_sp_scaling = 100
# --------------------------------------------------------------------
# Ramp_rate
Ramp_rate_percentage = 0.3
# --------------------------------------------------------------------
def bess_simulator():
    active_power_sp_old = 0
    # Connect to the log database
    # conn = psycopg2.connect(dbname="microgrid", user="postgres", password="postgres", host="127.0.0.1", port="5432")
    # cur = conn.cursor()
    # Create the server
    server = modbus_tcp.TcpServer(address=modbus_slave_ip_bess, port=modbus_slave_port)
    server.start()
    # Add slave
    slave_1 = server.add_slave(modbus_slave_id)
    # Add data blocks
    slave_1.add_block('A', cst.HOLDING_REGISTERS, 1, 4000)
    slave_1.add_block('B', cst.COILS, 1, 4000)
    # Voltage initialization
    voltage_v12_c = int2C(Voltage_V12[1], Voltage_V12[3])
    slave_1.set_values('A', Voltage_V12[0], voltage_v12_c)
    voltage_v23_c = int2C(Voltage_V23[1], Voltage_V23[3])
    slave_1.set_values('A', Voltage_V23[0], voltage_v23_c)
    voltage_v31_c = int2C(Voltage_V31[1], Voltage_V31[3])
    slave_1.set_values('A', Voltage_V31[0], voltage_v31_c)
    # Current initialization
    current_i1_c = int2C(Current_I1[1], Current_I1[3])
    slave_1.set_values('A', Current_I1[0], current_i1_c)
    current_i2_c = int2C(Current_I2[1], Current_I2[3])
    slave_1.set_values('A', Current_I2[0], current_i2_c)
    current_i3_c = int2C(Current_I3[1], Current_I3[3])
    slave_1.set_values('A', Current_I3[0], current_i3_c)
    # P\Q\F initialization
    active_power_c = int2C(Active_Power[1], Active_Power[3])
    slave_1.set_values('A', Active_Power[0], active_power_c)
    reactive_power_c = int2C(Reactive_Power[1], Reactive_Power[3])
    slave_1.set_values('A', Reactive_Power[0], reactive_power_c)
    frequency_c = int2C(Frequency[1], Frequency[3])
    slave_1.set_values('A', Frequency[0], frequency_c)
    # Energy initialization
    energy_c = int2C(energy[1], energy[3])
    slave_1.set_values('A', energy[0], energy_c)
    # SOC initialization
    soc_c = int2C(SOC[1], SOC[3])
    slave_1.set_values('A', SOC[0], soc_c)
    # SP_cmd initialization
    sp_cmd_c = int2C(SP_cmd[1], SP_cmd[3])
    slave_1.set_values('A', SP_cmd[0], sp_cmd_c)
    # Control initialization
    start_cmd_c = int2C(Start_cmd[1], Start_cmd[3])
    slave_1.set_values('B', Start_cmd[0], start_cmd_c)
    stop_cmd_c = int2C(Stop_cmd[1], Stop_cmd[3])
    slave_1.set_values('B', Stop_cmd[0], stop_cmd_c)
    alarm_rst_cmd_c = int2C(Alarm_rst_cmd[1], Alarm_rst_cmd[3])
    slave_1.set_values('B', Alarm_rst_cmd[0], alarm_rst_cmd_c)
    auto_mode_cmd_c = int2C(Auto_mode_cmd[1], Auto_mode_cmd[3])
    slave_1.set_values('B', Auto_mode_cmd[0], auto_mode_cmd_c)
    operator_mode_cmd_c = int2C(Operator_mode_cmd[1], Operator_mode_cmd[3])
    slave_1.set_values('B', Operator_mode_cmd[0], operator_mode_cmd_c)
    p_enable_cmd_c = int2C(P_enable_cmd[1], P_enable_cmd[3])
    slave_1.set_values('B', P_enable_cmd[0], p_enable_cmd_c)
    p_disable_cmd_c = int2C(P_disable_cmd[1], P_disable_cmd[3])
    slave_1.set_values('B', P_disable_cmd[0], p_disable_cmd_c)
    # Read setpoint and generate feedback
    # Status initialization
    reg_4_c = int2C(Reg_4[1], Reg_4[3])
    slave_1.set_values('A', Reg_4[0], reg_4_c)
    reg_5_c = int2C(Reg_5[1], Reg_5[3])
    slave_1.set_values('A', Reg_5[0], reg_5_c)
    # Status initialization
    max_charge_power_c = int2C(Max_charge_power[1], Max_charge_power[3])
    slave_1.set_values('A', Max_charge_power[0], max_charge_power_c)
    max_discharge_power_c = int2C(Max_discharge_power[1], Max_discharge_power[3])
    slave_1.set_values('A', Max_discharge_power[0], max_discharge_power_c)
    try:
        shm = shared_memory.SharedMemory(name=modbus_slave_ip_cb_bess, create=True, size=10)
    except BaseException:
        shm = shared_memory.SharedMemory(name=modbus_slave_ip_cb_bess, create=False, size=10)
    while True:
        print('--------------------------------')
        # Read voltage from slave memory, C structure
        voltage_v12_c = slave_1.get_values('A', Voltage_V12[0], Voltage_V12[2])
        voltage_v12_int = C2int(Voltage_V12[1], voltage_v12_c)
        voltage_v23_c = slave_1.get_values('A', Voltage_V23[0], Voltage_V23[2])
        voltage_v23_int = C2int(Voltage_V23[1], voltage_v23_c)
        voltage_v31_c = slave_1.get_values('A', Voltage_V31[0], Voltage_V31[2])
        voltage_v31_int = C2int(Voltage_V31[1], voltage_v31_c)
        # Read current from slave memory, C structure
        current_i1_c = slave_1.get_values('A', Current_I1[0], Current_I1[2])
        current_i1_int = C2int(Current_I1[1], current_i1_c)
        current_i2_c = slave_1.get_values('A', Current_I2[0], Current_I2[2])
        current_i2_int = C2int(Current_I2[1], current_i2_c)
        current_i3_c = slave_1.get_values('A', Current_I3[0], Current_I3[2])
        current_i3_int = C2int(Current_I3[1], current_i3_c)
        # Read P\Q\F from slave memory, C structure
        active_power_c = slave_1.get_values('A', Active_Power[0], Active_Power[2])
        active_power_int = C2int(Active_Power[1], active_power_c)
        reactive_power_c = slave_1.get_values('A', Reactive_Power[0], Reactive_Power[2])
        reactive_power_int = C2int(Reactive_Power[1], reactive_power_c)
        frequency_c = slave_1.get_values('A', Frequency[0], Frequency[2])
        frequency_int = C2int(Frequency[1], frequency_c)
        # Read SOC from slave memory, C structure
        soc_c = slave_1.get_values('A', SOC[0], SOC[2])
        soc_int = C2int(SOC[1], soc_c)
        # Read SP_cmd from slave memory, C structure
        sp_cmd_c = slave_1.get_values('A', SP_cmd[0], SP_cmd[2])
        sp_cmd_int = C2int(SP_cmd[1], sp_cmd_c)
        # if sp_cmd_int != active_power_sp_old:
        #     cur.execute(
        #         "INSERT INTO Control values(DEFAULT,now(),'{}','BESS_active_power_setpoint_changed_from_{}_to_{}')".format(
        #             modbus_slave_ip_bess, active_power_sp_old, sp_cmd_int))
        #     active_power_sp_old = sp_cmd_int
        #     conn.commit()
        # Read status from slave memory, C structure
        reg_4_c = slave_1.get_values('A', Reg_4[0], Reg_4[2])
        reg_4_int = C2int(Reg_4[1], reg_4_c)
        # Read Control from slave memory, C structure
        start_cmd_c = slave_1.get_values('B', Start_cmd[0], Start_cmd[2])
        start_cmd_int = C2int(Start_cmd[1], start_cmd_c)
        stop_cmd_c = slave_1.get_values('B', Stop_cmd[0], Stop_cmd[2])
        stop_cmd_int = C2int(Stop_cmd[1], stop_cmd_c)
        alarm_rst_cmd_c = slave_1.get_values('B', Alarm_rst_cmd[0], Alarm_rst_cmd[2])
        alarm_rst_cmd_int = C2int(Alarm_rst_cmd[1], alarm_rst_cmd_c)
        auto_mode_cmd_c = slave_1.get_values('B', Auto_mode_cmd[0], Auto_mode_cmd[2])
        auto_mode_cmd_int = C2int(Auto_mode_cmd[1], auto_mode_cmd_c)
        operator_mode_cmd_c = slave_1.get_values('B', Operator_mode_cmd[0], Operator_mode_cmd[2])
        operator_mode_cmd_int = C2int(Operator_mode_cmd[1], operator_mode_cmd_c)
        p_enable_cmd_c = slave_1.get_values('B', P_enable_cmd[0], P_enable_cmd[2])
        p_enable_cmd_int = C2int(P_enable_cmd[1], p_enable_cmd_c)
        p_disable_cmd_c = slave_1.get_values('B', P_disable_cmd[0], P_disable_cmd[2])
        p_disable_cmd_int = C2int(P_disable_cmd[1], p_disable_cmd_c)
        print('Status update:')
        print('Voltage_V12:', voltage_v12_int, 'VAC')
        print('Voltage_V23:', voltage_v23_int, 'VAC')
        print('Voltage_V31:', voltage_v31_int, 'VAC')
        print('Current_I1:', current_i1_int, 'A')
        print('Current_I2:', current_i2_int, 'A')
        print('Current_I3:', current_i3_int, 'A')
        print('Active_Power:', active_power_int, 'kW')
        print('Reactive_Power:', reactive_power_int, 'kVAR')
        print('Frequency:', frequency_int, 'Hz')
        print('SOC:', soc_int, '%')
        print('SP_cmd:', sp_cmd_int, 'kW')
        print('Start_cmd:', start_cmd_int)
        print('Stop_cmd:', stop_cmd_int)
        print('Alarm_rst_cmd:', alarm_rst_cmd_int)
        print('Auto_mode_cmd:', auto_mode_cmd_int)
        print('Operator_mode_cmd:', operator_mode_cmd_int)
        print('P_enable_cmd:', p_enable_cmd_int)
        print('P_disable_cmd:', p_disable_cmd_int)
        # if CB open, stop calculation
        cb_status = shm.buf[0]
        if cb_status == 4:
            active_power_int = 0
        # else start the calculation
        else:
            if 0 < soc_int < 100:
                soc_int = soc_int - (sp_cmd_int / 300)
                active_power_int = sp_cmd_int
            elif soc_int <= 0:
                if sp_cmd_int < 0:
                    soc_int = soc_int - (sp_cmd_int / 300)
                else:
                    soc_int = 0
                    active_power_int = 0
            elif soc_int >= 100:
                if sp_cmd_int > 0:
                    soc_int = soc_int - (sp_cmd_int / 300)
                else:
                    soc_int = 100
                    active_power_int = 0

        soc_c = int2C(SOC[1], soc_int)
        slave_1.set_values('A', SOC[0], soc_c)
        active_power_c = int2C(Active_Power[1], active_power_int)
        slave_1.set_values('A', Active_Power[0], active_power_c)
        # send P to CB
        active_power_c = int2C(Active_Power[1], active_power_int)
        slave_1.set_values('A', Active_Power[0], active_power_c)
        # send active power to shared memory for CB simulator use
        active_power_memory = int2C('float32', scaling_cb*active_power_int)
        shm.buf[1] = active_power_memory[0] // 256
        shm.buf[2] = active_power_memory[0] % 256
        shm.buf[3] = active_power_memory[1] // 256
        shm.buf[4] = active_power_memory[1] % 256
        SOC_memory = int2C('float32', soc_int)
        shm.buf[5] = SOC_memory[0] // 256
        shm.buf[6] = SOC_memory[0] % 256
        shm.buf[7] = SOC_memory[1] // 256
        shm.buf[8] = SOC_memory[1] % 256
        print('memory:',shm, shm.buf[1], shm.buf[2], shm.buf[3], shm.buf[4])
        SP_cmd_f_c = int2C(SP_cmd_f[1], sp_cmd_int)
        slave_1.set_values('A', SP_cmd_f[0], SP_cmd_f_c)
        print(list(map(int, list(bin(reg_4_int))[2:])))
        Reg_4_value = list(map(int, list(bin(reg_4_int))[2:]))
        Reg_4_value.reverse()
        print(Reg_4_value)
        (Running, Starting, Stopping, Stopped, Online, Auto_Mode_Active, Manual_Mode_Active, Operator_Mode_Active,
         AC_CB_Closed, Alarms_Healthy) = Reg_4_value
        if start_cmd_int == 1 and stop_cmd_int == 0:
            Running = 1
            Stopped = 0
            Online = 1
        elif start_cmd_int == 0 and stop_cmd_int == 1:
            Running = 0
            Stopped = 1
            Online = 0

        if operator_mode_cmd_int == 1:
            Operator_Mode_Active = 1
        else:
            Operator_Mode_Active = 0
        reg_4_int = Alarms_Healthy * 512 + AC_CB_Closed * 256 + Operator_Mode_Active * 128 + Manual_Mode_Active * 64 + Auto_Mode_Active * 32 + Online * 16 + Stopped * 8 + Stopping * 4 + Starting * 2 + Running
        reg_4_c = int2C(Reg_4[1], reg_4_int)
        slave_1.set_values('A', Reg_4[0], reg_4_c)

        if p_enable_cmd_int == 1:
            reg_5_c = int2C(Reg_5[1], 4096)
            slave_1.set_values('A', Reg_5[0], reg_5_c)
        else:
            reg_5_c = int2C(Reg_5[1], 0)
            slave_1.set_values('A', Reg_5[0], reg_5_c)
        print('Running:', Running)
        print('Stopped:', Stopped)
        print('Online:', Online)
        print('Operator_Mode_Active:', Operator_Mode_Active)

        if active_power_int == 0:
            current_i1_int = 0
        else:
            current_i1_int = 1000*1.732 * active_power_int / (3 * voltage_v12_int)
        current_i1_c = int2C(Current_I1[1], current_i1_int)
        slave_1.set_values('A', Current_I1[0], current_i1_c)
        slave_1.set_values('A', Current_I2[0], current_i1_c)
        slave_1.set_values('A', Current_I3[0], current_i1_c)
        time.sleep(1)


if __name__ == "__main__":
    bess_simulator()
