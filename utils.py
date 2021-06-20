import serial
import csv
import config


class Reader:
    def __init__(self):
        self.serial_port = serial.Serial(config.port, config.baud_rate, timeout=1)
        self.serial_port.bytesize = 8
        self.serial_port.xonxoff = True
        self.serial_port.rtscts = False
        self.serial_port.dsrdtr = True
        self.step = 0.001
        self.file = open("data.csv", "w+", newline='')
        self.writer = csv.writer(self.file)

    def read_all(self):
        while True:
        #for i in range(10):
            parsed = self.parse_line()
            lat, lon, values = parsed
            print(lat, lon, values)

    # step tylko żeby sprawdzać czy działa animacja mapy, bo w obecnych danych współrzędne sie nie zmieniają
    def parse_coords(self, raw_lon, raw_lat):
        self.step += 0.001
        return raw_lon / 10000000 + self.step, raw_lat / 10000000 + self.step

    def parse_line(self):
        while True:

            raw_line = self.serial_port.readline()
            print(raw_line)
            decoded_line = raw_line.decode('utf-8', 'ignore').strip('\r\n').replace(",", ", ").replace("  ", " ").split(' ')
            if ',' not in decoded_line:
                value_list = [float(val.strip(',')) for val in decoded_line if val]
                if len(value_list) == config.columns_num:
                    lat, lon = self.parse_coords(*value_list[:2])
                    values = value_list[2:]
                    self.writer.writerow([lat, lon] + values)
                    return lat, lon, values

    def close(self):
        self.serial_port.close()
        self.file.close()


#
# rd = Reader()
# rd.read_all()
# rd.close()
