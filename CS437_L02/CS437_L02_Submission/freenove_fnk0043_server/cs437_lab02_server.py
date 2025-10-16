'''
Minqiang Liu (mliu110), Yi Zhang (yjzhang2)
20251014
cs437_lab02_server.py

Uses the following Freenove FNK0043 libraries:
- car.py
- command.py
- message.py
- motor.py
- server.py
- tcp_server.py
- Thread.py
- ultrasonic.py

Modified `command.py` to create a dummy get temperature command
'''
import time
import math
import signal
import threading
import queue
from server import Server
from message import Message_Parse
from command import Command
from car import Car
from threading import Thread
from camera import Camera			# extremely low-frame rate video == image l0l
	# use either `get_frame` OR `save_image`?
from gpiozero import CPUTemperature, LoadAverage
	# for getting the rpi cpu temperature
	# https://gpiozero.readthedocs.io/en/stable/api_internal.html

class CarTCPServer:
	def __init__(self):
		# Core components
		self.tcp_server = Server()
		self.command = Command()
		self.car = Car()

		# Command parsing
		self.rx_queue: "queue.Queue[str]" = queue.Queue()
		self.parser = Message_Parse()

		# Lifecycle
		self.stop_event = threading.Event()
		self.rx_thread = None
		self.work_thread = None
		self.rx_running = False
		self.work_running = False

		# Rotation helper state
		self.rotation_active = False
		self.send_sonic_data_time = time.time()


	def send_sonic_data(self):
		if time.time() - self.send_sonic_data_time > 0.5:
			self.send_sonic_data_time = time.time()
			if self.tcp_server.get_command_server_busy() == False:
				distance = self.car.sonic.get_distance()
				cmd = self.command.CMD_MODE + "D#3#{:.2f}".format(distance) + "\n"
				self.tcp_server.send_data_to_command_client(cmd)
				#print(cmd)

	def send_cpu_temperature_data(self):
		# todo, refactor `send_sonic_data()`, this, `send_cpu_load_data()` into a general method
		cpu_temperature_obj = CPUTemperature()
		temperature = cpu_temperature_obj.temperature
		if not self.tcp_server.get_command_server_busy():
			message = f'{self.command.CMD_TEMPERATURE}#{temperature}\n'
			self.tcp_server.send_data_to_command_client(message)
	
	def send_cpu_load_data(self):
		cpu_load_obj = LoadAverage(min_load_average = 0, max_load_average = 2)
		cpu_max_load = cpu_load_obj.max_load_average
		if not self.tcp_server.get_command_server_busy():
			message = f'{self.command.CMD_CPU_LOAD}#{cpu_max_load}\n'
			self.tcp_server.send_data_to_command_client(message)

	def send_power_data(self):
		if self.tcp_server.get_command_server_busy() == False:
			power = self.car.adc.read_adc(2) * (3 if self.car.adc.pcb_version == 1 else 2)
			cmd = self.command.CMD_POWER + "#" + str(power) + "\n"
			self.tcp_server.send_data_to_command_client(cmd)
			#print(cmd)

	# ----------------------------- Threads -----------------------------
	def _start_thread(self, attr_name, target):
		t = getattr(self, attr_name)
		if t is None or not t.is_alive():
			th = threading.Thread(target=target, daemon=True)
			setattr(self, attr_name, th)
			th.start()

	def _stop_thread(self, attr_name, join_timeout=0.3):
		t = getattr(self, attr_name)
		if t is not None and t.is_alive():
			t.join(join_timeout)
		setattr(self, attr_name, None)

	# Receive from TCP server; normalize into one-line commands
	def threading_receive(self):
		self.rx_running = True
		while self.rx_running and not self.stop_event.is_set():
			cmd_queue = self.tcp_server.read_data_from_command_server()
			if cmd_queue.qsize() > 0:
				client_addr, raw = cmd_queue.get()
				text = (raw or "").strip()
				if not text:
					continue
				if "\n" in text:
					for line in text.split("\n"):
						if line:
							self.rx_queue.put(line)
				else:
					self.rx_queue.put(text)
			else:
				time.sleep(0.001)

	# Dispatch loop: handle only movement-related commands
	def threading_work(self):
		self.work_running = True
		while self.work_running and not self.stop_event.is_set():
			try:
				line = self.rx_queue.get(timeout=0.05)
			except queue.Empty:
				continue

			try:
				self.parser.clear_parameters()
				self.parser.parse(line)
				cmd = self.parser.command_string
				ints = self.parser.int_parameter
				print(cmd)


				# ---- ONLY movement commands are honored ----
				if cmd == self.command.CMD_MOTOR:
					# Direct duty for 4 wheels
					d = [int(ints[i]) for i in range(4)]
					self.car.motor.set_motor_model(d[0], d[1], d[2], d[3])

				elif cmd == self.command.CMD_SONIC:
					self.send_sonic_data()  # Send ultrasonic distance data

				elif cmd == self.command.CMD_TEMPERATURE:
					self.send_cpu_temperature_data()

				elif cmd == self.command.CMD_CPU_LOAD:
					self.send_cpu_load_data()

				elif cmd == self.command.CMD_POWER:
					self.send_power_data()  # Send power level data to client

				elif cmd == self.command.CMD_M_MOTOR:
					# Mecanum polar vector control
					# ints: [angle_deg, mag, rot_angle_deg, rot_mag]
					d = [int(ints[i]) for i in range(4)]
					LX = -int(d[1] * math.sin(math.radians(d[0])))
					LY =  int(d[1] * math.cos(math.radians(d[0])))
					RX =  int(d[3] * math.sin(math.radians(d[2])))
					RY =  int(d[3] * math.cos(math.radians(d[2])))
					FR = LY - LX + RX
					FL = LY + LX - RX
					BL = LY - LX - RX
					BR = LY + LX + RX
					self.car.motor.set_motor_model(FL, BL, FR, BR)
			
				elif cmd == self.command.CMD_MODE:
					# Only honor "stop motors" (0). Ignore all other modes/features.
					v = int(ints[0])
					if v == 0:
						self.car.motor.set_motor_model(0, 0, 0, 0)

				else:
					# Ignore any non-movement command silently
					pass

			except Exception as e:
				print(f"[MOVE ERROR] {e}")

	# ----------------------------- Lifecycle -----------------------------
	def start(self):
		print("[MovementOnly] Starting command server!")
		self.tcp_server.start_tcp_servers()  # Only the command port matters
		self._start_thread("rx_thread", self.threading_receive)
		self._start_thread("work_thread", self.threading_work)
		print("[MovementOnly] Running. Press Ctrl+C to stop.")

	def stop(self):
		print("[MovementOnly] Stopping!")
		self.stop_event.set()

		self.rx_running = False
		self.work_running = False

		self._stop_thread("rx_thread")
		self._stop_thread("work_thread")

		# Stop TCP server
		try:
			self.tcp_server.stop_tcp_servers()
		except Exception:
			pass
		self.tcp_server = None

		# Ensure motors are stopped and hardware is closed
		try:
			self.car.motor.set_motor_model(0, 0, 0, 0)
		except Exception:
			pass
		try:
			self.car.close()
		except Exception:
			pass

		print("[MovementOnly] Stopped.")


def main():
	srv = CarTCPServer()

	def on_sig(sig, frame):
		print("\nCaught signal, shutting down!")	# â€¦?
		srv.stop()

	signal.signal(signal.SIGINT, on_sig)
	signal.signal(signal.SIGTERM, on_sig)

	srv.start()
	try:
		while not srv.stop_event.is_set():
			time.sleep(0.2)
	finally:
		srv.stop()


if __name__ == "__main__":
	main()
