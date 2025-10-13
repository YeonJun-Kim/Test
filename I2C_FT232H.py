import pyftdi
from pyftdi import i2c



Slave_Address = 0x64 # Slave Address (IO Expander)

try:
	I2C_Controller = i2c.I2cController()
	I2C_Controller.configure('ftdi://ftdi:232h:1/1', frequency = 800e3) # Configuration : ftdi url + I2C frequency

except Exception as e:
	print(e)

Device = I2C_Controller.get_port(Slave_Address)

# print(Device.read_from(0xb4, 1))




# For exchanging data with the I2C device, you have the 'exchange', 'write', 'write_to', 'read' and 'read_from' methods. You can refer to this for more details: https://eblot.github.io/pyftdi/api/i2c.html#pyftdi.i2c.I2cPort.read
# Example: reading 'nb_bytes' bytes from the device register at address 'register_address'. Returns an array of bytes:



###### IO Expander I2C Communication ########################
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
##############################################################
