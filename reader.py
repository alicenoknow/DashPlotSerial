from collections import deque
from queue import Queue

import serial
import csv
import config


class Reader:
    def __init__(self):
        self.serial_port = serial.Serial(config.port, config.baud_rate, timeout=1)
        self.file = open("data.csv", "w+", newline='')
        self.writer = csv.writer(self.file)
        self.data_dequeues = [deque(maxlen=config.data_len) for _ in range(config.columns_num)]

    def read_all(self):
        while True:
        #for i in range(10):
            parsed = self.parse_line()
            lat, lon, values = parsed
            print(lat, lon, values)

    def parse_coords(self, raw_lon, raw_lat):
        return raw_lon / 10000000, raw_lat / 10000000

    def parse_line(self):
        while True:

            raw_line = self.serial_port.readline()
            decoded_line = raw_line.decode('utf-8', 'ignore').strip('\r\n').replace(",", ", ").replace("  ", " ").split(' ')
            if ',' not in decoded_line:
                value_list = [float(val.strip(',')) for val in decoded_line if val]
                if len(value_list) == config.columns_num:
                    lat, lon = self.parse_coords(*value_list[:2])
                    values = value_list[2:]
                    self.writer.writerow([lat, lon] + values)
                    for idx, val in enumerate(values):
                        self.data_dequeues[idx].append(val)
                    return lat, lon, values

    def data_to_send(self):
        lat, lon, _ = self.parse_line()
        values = [list(dq) for dq in self.data_dequeues]
        return {
            "lat": lat,
            "lon": lon,
            "values": values
        }

    def close(self):
        self.serial_port.close()
        self.file.close()


def reader_main(rx_queue: Queue, tx_queue: Queue) -> None:
    try:
        running = True
        reader = Reader()
        tx_queue.put(("OK", {}))

        while running:
            cmd, args = rx_queue.get()

            if cmd == 'DATA':
                tx_queue.put((cmd, reader.data_to_send()))

            if cmd == 'EXIT':
                reader.close()
                return
    except serial.SerialException:
        tx_queue.put(("ERROR", {"Cannot open serial port"}))
        exit(-1)


# rd = Reader()
# rd.read_all()
# rd.close()
