A Microgrid testing framework

As microgrid project profit is always not that good, the buget for onsite commisisoning is very small. Then microgrid controller is usually configured and tested in Lab, without DER connecton.

We can't have all those DERs installed in the lab but we need to verify the microgrid control logic and communication.

So I develop this tool to simulate a microgrid.


1. PV simulator (Modbus TCP): It can communicate with microgrid controller and calculate P output accordingly.

2. BESS simulator (Modbus TCP): It can communicate with microgrid controller and calculate P and SOC accordingly.

3. CHP simulator (Modbus TCP): It can communicate with microgrid controller and calculate P accordingly.

4. CB simulator (Modbus TCP): Each DER comes with a smart CB. Microgrid controller can send Open/Close commands to them.

5. Screenshot: This script will record key data and save them into a database for further analysis.


![Microgrid testing](https://user-images.githubusercontent.com/29573181/229689515-9541e6fe-83bb-46e1-aa7b-a7e589bcf6fa.jpg)
