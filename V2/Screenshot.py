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
modbus_slave_ip_cb_utility = "172.168.200.1"
modbus_slave_ip_cb_load = "172.168.200.2"
modbus_slave_ip_cb_chp = "172.168.200.5"
modbus_slave_ip_cb_pv = "172.168.200.3"
modbus_slave_ip_cb_bess = '172.168.200.4'

Scaling_utility = 0.1
Scaling_load = 0.1
Scaling_chp = 0.1
Scaling_pv = 0.1
Scaling_bess = 0.1

# ------------------------------------------------------------------------------

def Screenshot():
    # Connect to the log database
    conn = psycopg2.connect(dbname="microgrid", user="postgres", password="postgres", host="127.0.0.1", port="5432")
    cur = conn.cursor()
    while True:
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
        active_power_utility_c = [shm_cb_utility.buf[1] * 256 + shm_cb_utility.buf[2], shm_cb_utility.buf[3] * 256 + shm_cb_utility.buf[4]]
        active_power_utility_int = C2int('float32', active_power_utility_c)*Scaling_utility
        active_power_load_c = [shm_cb_load.buf[1] * 256 + shm_cb_load.buf[2], shm_cb_load.buf[3] * 256 + shm_cb_load.buf[4]]
        active_power_load_int = C2int('float32', active_power_load_c)*Scaling_load
        active_power_chp_c = [shm_cb_chp.buf[1] * 256 + shm_cb_chp.buf[2], shm_cb_chp.buf[3] * 256 + shm_cb_chp.buf[4]]
        active_power_chp_int = C2int('float32', active_power_chp_c)*Scaling_chp
        active_power_pv_c = [shm_cb_pv.buf[1] * 256 + shm_cb_pv.buf[2], shm_cb_pv.buf[3] * 256 + shm_cb_pv.buf[4]]
        active_power_pv_int = C2int('float32', active_power_pv_c)*Scaling_pv
        active_power_bess_c = [shm_cb_bess.buf[1] * 256 + shm_cb_bess.buf[2], shm_cb_bess.buf[3] * 256 + shm_cb_bess.buf[4]]
        active_power_bess_int = C2int('float32', active_power_bess_c)*Scaling_bess
        soc_c = [shm_cb_bess.buf[5] * 256 + shm_cb_bess.buf[6], shm_cb_bess.buf[7] * 256 + shm_cb_bess.buf[8]]
        soc_int = C2int('float32', soc_c)
        print(active_power_utility_int)
        print(active_power_load_int)
        print(active_power_chp_int)
        print(active_power_pv_int)
        print(active_power_bess_int)
        cur.execute(
            "INSERT INTO RealTime values(DEFAULT,now(),'{}','{}','{}','{}','{}','{}')".format(active_power_utility_int,active_power_load_int,active_power_chp_int,active_power_pv_int,active_power_bess_int,soc_int))
        conn.commit()
        time.sleep(0.2)

if __name__ == "__main__":
    Screenshot()
