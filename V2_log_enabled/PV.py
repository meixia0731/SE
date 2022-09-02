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
modbus_slave_ip_pv = '172.168.200.8'
# PV_CB address. PV will get CB status from this memory and send P to this memory
modbus_slave_ip_cb_pv = "172.168.200.3"
scaling_cb = -10
# Listening port
modbus_slave_port = 502
# Listening slave ID
modbus_slave_id = 1
# --------------------------------------------------------------------
# Modbus data points configuration, [modbus_address, data_type, length, initial_value]
active_power_addr = [8069, 'uint64', 4, 0]
reactive_power_addr = [8075, 'int64', 4, 300]
limitation_power_addr = [8085, 'uint32', 2, 1000]
start_stop_status_addr = [8067, 'uint16', 1, 1]
start_stop_cmd_addr = [8001, 'uint16', 1, 1]
active_power_sp_addr = [8002, 'uint32', 2, 1000]
energy_addr = [8079, 'uint64', 4, 30000]
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
def pv_simulator():
    start_stop_cmd_old = 0
    active_power_sp_old = 0
    # Connect to the log database
    conn = psycopg2.connect(dbname="microgrid", user="postgres", password="postgres", host="192.9.163.61", port="5432")
    cur = conn.cursor()
    # Create the modbus slave server
    server = modbus_tcp.TcpServer(address=modbus_slave_ip_pv, port=modbus_slave_port)
    # Start the modbus slave server
    server.start()
    # Create the modbus slave instance
    slave_1 = server.add_slave(modbus_slave_id)
    # Create two data block, A for function code 4, B for function code 3.
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
    # Send above C structure data to memory. Then Modbus client can read the default value from these addresses.
    slave_1.set_values('A', active_power_addr[0], active_power_c)
    slave_1.set_values('A', reactive_power_addr[0], reactive_power_c)
    slave_1.set_values('A', limitation_power_addr[0], limitation_power_c)
    slave_1.set_values('A', start_stop_status_addr[0], start_stop_status_c)
    slave_1.set_values('B', start_stop_cmd_addr[0], start_stop_cmd_c)
    slave_1.set_values('B', active_power_sp_addr[0], active_power_sp_c)
    slave_1.set_values('A', energy_addr[0], energy_c)
    # Create or attach to the PV_CB memory to exchange CB status and P.
    # PV simulator get CB status from PV_CB memory. PV_CB simulator get P from PV simulator
    try:
        # if PV_CB memory does not exist, create it
        shm = shared_memory.SharedMemory(name=modbus_slave_ip_cb_pv, create=True, size=10)
    except BaseException:
        # if PV_CB memory exist, load it
        shm = shared_memory.SharedMemory(name=modbus_slave_ip_cb_pv, create=False, size=10)
    # Logic engine starts from here
    while True:
        print('--------------------------------')
        # Read below data from slave memory, C structure
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

        # Print logic inputs of this circle
        print('Engine Inputs:')
        print('active_power:', active_power_int, 'W')
        print('reactive_power:', reactive_power_int, 'Var')
        print('limitation_power:', limitation_power_int, 'W')
        print('start_stop_status:', status_str[start_stop_status_int])
        print('start_stop_cmd:', cmd_str[start_stop_cmd_int])
        print('active_power_setpoint:', active_power_sp_int, 'W')
        print('energy_int:', energy_int, 'Wh')

        # if new start or stop command received, add them into log database
        if start_stop_cmd_int != start_stop_cmd_old:
            cur.execute(
                "INSERT INTO Control values(DEFAULT,now(),'{}','PV_start_stop_cmd_changed_from_{}_to_{}')".format(
                    modbus_slave_ip_pv, start_stop_cmd_old, start_stop_cmd_int))
            start_stop_cmd_old = start_stop_cmd_int
            conn.commit()
        # if new setpoint received, add them into log database
        if active_power_sp_int != active_power_sp_old:
            cur.execute(
                "INSERT INTO Control values(DEFAULT,now(),'{}','PV_active_power_setpoint_changed_from_{}_to_{}')".format(
                    modbus_slave_ip_pv, active_power_sp_old, active_power_sp_int))
            active_power_sp_old = active_power_sp_int
            conn.commit()

        # if stop command received, change P setpoint to zero. New P = P + (P_setpint-P)*Ramp_rate
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
        # if CB open, force active power to zero.
        cb_status = shm.buf[0]
        if cb_status == 4:
            active_power_int = 0
        active_power_c = int2C(active_power_addr[1], active_power_int)
        slave_1.set_values('A', active_power_addr[0], active_power_c)
        # send active power to shared memory for CB simulator use
        active_power_memory = int2C('float32', scaling_cb*active_power_int)
        shm.buf[1] = active_power_memory[0] // 256
        shm.buf[2] = active_power_memory[0] % 256
        shm.buf[3] = active_power_memory[1] // 256
        shm.buf[4] = active_power_memory[1] % 256
        print('memory:',shm, shm.buf[1], shm.buf[2], shm.buf[3], shm.buf[4])
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


if __name__ == "__main__":
    pv_simulator()
