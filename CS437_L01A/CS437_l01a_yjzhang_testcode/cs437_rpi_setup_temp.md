cd
git clone --depth 1 https://github.com/Freenove/Freenove_4WD_Smart_Car_Kit_for_Raspberry_Pi

## setup py3 as default dir
cd /usr/bin
sudo rm python
sudo ln -s python3 python
<!-- Check python --->
python

# S02 Enable I2C and VNC
https://docs.freenove.com/projects/fnk0043/en/latest/fnk0043/codes/tutorial/1_Software_installation.html

## spi, to check spi version:
gpio -v
if spi v1.0,then disable; if spi v2.0, then able

## check i2c is enabled
lsmod | grep i2c

## install i2c tools
sudo apt-get install i2c-tools

## install python-smbus
sudo apt-get install python3-smbus

## comm test
i2cdetect -y 1

## if rpi<4: disable audio, o.w. leds won't work properly
sudo nano /etc/modprobe.d/snd-blacklist.conf
blacklist snd_bcm2835
sudo nano /boot/config.txt
<!--Look FOR (use CTRL+W in `nano`
# Enable audio (loads snd_bcm2835)
dtparam=audio=on

and change to

# Enable audio (loads snd_bcm2835)
# dtparam=audio=on
-->
CTRL O CTRL X, restart

# 03 Install Libraries
cd ~/Freenove_4WD_Smart_Car_Kit_for_Raspberry_Pi/Code
sudo python setup.py
<!-- Camera setup rpi is kit is: ov5647 -->
sudo reboot <!-- after done installin libraries -->
sudo python setup.py <!-- to restart installation if network err-->

# 04 Build RPI CAR
done

# TEST CAR
Documentation Link: [Freenove FNK0043 Module Test](https://docs.freenove.com/projects/fnk0043/en/latest/fnk0043/codes/tutorial/3_Module_test.html)
## Motor
cd ~/Freenove_4WD_Smart_Car_Kit_for_Raspberry_Pi/Code/Server
<!-- test motor -->
sudo python test.py Motor
<!-- If the direction is reversed, it moves back then move forward, please follow steps below., open `Freenove_4WD_Smart_Car_Kit_for_Raspberry_Pi/Code/Server/Motor.py` and add a negative for set motor_model