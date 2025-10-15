CS437_L02_BT_Setup
1. Update and Install Bluetooth-Related Packages
Run the following commands in the terminal to update the system and install Bluetooth components:
```sh
sudo apt update
sudo apt install -y pi-bluetooth bluez blueman
```

2. These packages provide Bluetooth hardware support, the Bluetooth protocol stack (BlueZ), and a graphical Bluetooth manager (Blueman). 
Start and Enable Bluetooth Service at Boot.
Run the command below to start the Bluetooth service immediately and set it to start automatically when the system boots:
```sh
sudo systemctl enable --now bluetooth
```

3. Verify Bluetooth Service Status
Use the following command to check whether the Bluetooth service is running successfully:
```sh
systemctl status bluetooth
```
If the output shows active (running), the Bluetooth service is working properly.


# Bluetooth Communication
1. (1-2): Configure rPi for BT SPP and Make it Pairable
The above:
```sh
sudo systemctl enable bluetooth
sudo systemctl start bluetooth
```
