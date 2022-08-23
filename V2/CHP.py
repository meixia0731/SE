import time
import modbus_tk.defines as cst
import modbus_tk.modbus_tcp as modbus_tcp
import psycopg2
import random
from multiprocessing import shared_memory
from data_type_converter import int2C as int2C
from data_type_converter import C2int as C2int

# --------------------------------------------------------------------
# Listening IP address
modbus_slave_ip_chp = '172.168.200.9'
# PV_CB address. PV will get CB status from this memory and send P to this memory
modbus_slave_ip_cb_chp = "172.168.200.5"
# Listening port
modbus_slave_port = 502
# Listening slave ID
modbus_slave_id = 1
# --------------------------------------------------------------------
# Modbus data points configuration, [modbus_address, data_type, length, initial_value]
active_power_sp_addr = [1030, 'uint16', 1, ]
start_stop_cmd_addr = [1025, 'int16', 1, 0]
start_status_addr = [36.5, 'int16', 1, 0]
remote_mode_addr = [36.8, 'int16', 1, 1]
stop_status_addr = [38.3, 'int16', 1, 1]
active_power_addr = [48, 'int16', 1, 0]
health_addr = [1.7, 'int16', 1, 0]
energy_addr = [50, 'uint32', 2, 0]
# --------------------------------------------------------------------
# Scaling, not in use
# --------------------------------------------------------------------
# Ramp_rate
Ramp_rate_percentage = 0.3
# --------------------------------------------------------------------
# Status dictionary
cmd_str = {0: 'Stop', 1: 'Start'}
status_str = {0: 'Stopped', 1: 'Started'}


# --------------------------------------------------------------------
def chp_simulator():
    start_stop_cmd_old = 0
    active_power_sp_old = 0
    # Connect to the log database
    conn = psycopg2.connect(dbname="microgrid", user="postgres", password="postgres", host="127.0.0.1", port="5432")
    cur = conn.cursor()
    # Create the modbus slave server
    server = modbus_tcp.TcpServer(address=modbus_slave_ip_chp, port=modbus_slave_port)
    # Start the modbus slave server
    server.start()
    # Create the modbus slave instance
    slave_1 = server.add_slave(modbus_slave_id)
    # Create two data block, A for function code 4, B for function code 3.
    slave_1.add_block('A', cst.ANALOG_INPUTS, 1, 1000)
    # Initialization, convert data to C structure
    active_power_sp_c = int2C(active_power_sp_addr[1], active_power_sp_addr[3])
    start_stop_cmd_c = int2C(start_stop_cmd_addr[1], start_stop_cmd_addr[3])
    active_power_c = int2C(active_power_addr[1], active_power_addr[3])

    # Send above C structure data to memory. Then Modbus client can read the default value from these addresses.
    slave_1.set_values('A', active_power_addr[0], active_power_sp_c)
    slave_1.set_values('A', start_stop_cmd_addr[0], start_stop_cmd_c)
    slave_1.set_values('A', active_power_addr[0], active_power_c)

    # Logic engine starts from here
    while True:
        # Create or attach to the PV_CB memory to exchange CB status and P.
        # PV simulator get CB status from PV_CB memory. PV_CB simulator get P from PV simulator
        try:
            # if PV_CB memory does not exist, create it
            shm = shared_memory.SharedMemory(name=modbus_slave_ip_cb_chp, create=True, size=10)
        except BaseException:
            # if PV_CB memory exist, load it
            shm = shared_memory.SharedMemory(name=modbus_slave_ip_cb_chp, create=False, size=10)
        print('--------------------------------')
        # Read below data from slave memory, C structure
        active_power_sp_c = slave_1.get_values('A', active_power_sp_addr[0], active_power_sp_addr[2])
        start_stop_cmd_c = slave_1.get_values('A', start_stop_cmd_addr[0], start_stop_cmd_addr[2])
        active_power_c = slave_1.get_values('A', active_power_addr[0], active_power_addr[2])


        # Convert C structure to INT, as engine inputs
        active_power_sp_int = C2int(active_power_sp_addr[1], active_power_sp_c)
        start_stop_cmd_int = C2int(start_stop_cmd_addr[1], start_stop_cmd_c)
        active_power_int = C2int(active_power_addr[1], active_power_c)

        # Print logic inputs of this circle
        print('Engine Inputs:')
        print('active_power_etpoint:', active_power_int, 'kW')
        print('Start_Stop Command:', start_stop_cmd_int, )
        print('active_powerSetpoint:', active_power_int, 'kW')


        # if new start or stop command received, add them into log database
        if start_stop_cmd_int != start_stop_cmd_old:
            cur.execute(
                "INSERT INTO sim_log values(DEFAULT,now(),'{}','start_stop_cmd_changed_from_{}_to_{}')".format(
                    modbus_slave_ip_chp, start_stop_cmd_old, start_stop_cmd_int))
            start_stop_cmd_old = start_stop_cmd_int
            conn.commit()
        # if new setpoint received, add them into log database
        if active_power_sp_int != active_power_sp_old:
            cur.execute(
                "INSERT INTO sim_log values(DEFAULT,now(),'{}','active_power_setpoint_changed_from_{}_to_{}')".format(
                    modbus_slave_ip_chp, active_power_sp_old, active_power_sp_int))
            active_power_sp_old = active_power_sp_int
            conn.commit()

        # if stop command received, change P setpoint to zero. New P = P + (P_setpint-P)*Ramp_rate
        if start_stop_cmd_int == 0:
            active_power_int = 0
        elif start_stop_cmd_int == 1:
            active_power_int = active_power_sp_int
        else:
            print('cmd input out of range, 0 for stop, 1 for start')
        # if CB open, force active power to zero.
        cb_status = shm.buf[0]
        if cb_status == 4:
            active_power_int = 0
        active_power_c = int2C(active_power_addr[1], active_power_int)
        slave_1.set_values('A', active_power_addr[0], active_power_c)
        # send active power to shared memory for CB simulator use
        active_power_memory = int2C('float32', active_power_int)
        shm.buf[1] = active_power_memory[0] // 256
        shm.buf[2] = active_power_memory[0] % 256
        shm.buf[3] = active_power_memory[1] // 256
        shm.buf[4] = active_power_memory[1] % 256
        shm.close()
        time.sleep(1)


if __name__ == "__main__":
    chp_simulator()
