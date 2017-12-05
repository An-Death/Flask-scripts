from datetime import datetime, timedelta


class Meta:
    def __repr__(self):
        return '<class.{}({})>'.format(self.__class__.__name__, self.__str__())


class Dt(Meta):
    formats = {'date': '%Y-%m-%d', 'datetime': '%Y-%m-%d %H:%M:%S'}

    def __init__(self, dt):
        if isinstance(dt, Dt):
            self.dt = dt.to_timestamp()
        elif isinstance(dt, int):
            if len(str(dt)) > 10:
                dt = int(str(dt)[:10])
            self.dt = dt
        elif isinstance(dt, datetime):
            self.dt = int(datetime.timestamp(dt))
        elif isinstance(dt, str):
            if dt.isdigit():
                self.dt = int(dt[:10])
            elif len(dt) > 10:
                try:
                    self.dt = datetime.strptime(dt, Dt.formats['datetime']).timestamp()
                except ValueError:
                    self.dt = datetime.strptime(dt, Dt.formats['datetime'] + '.%f').timestamp()
                self.dt = int(self.dt)
            else:
                self.dt = datetime.strptime(dt, Dt.formats['date']).timestamp()
                self.dt = int(self.dt)
        else:
            raise ValueError('Не получилось распознать dt {}, type({})'.format(dt, type(dt)))

    def __str__(self):
        year = Dt('2000-01-01').to_timestamp()
        return self.to_string() if self.dt > year else self.to_human()

    def __float__(self):
        return float(self.dt)

    def __sub__(self, other):
        if isinstance(other, Dt):
            other = other.dt
        return Dt(self.dt - other)

    def __int__(self):
        return self.to_timestamp()

    def __add__(self, other):
        if isinstance(other, Dt):
            other = other.dt
        elif isinstance(other, str) and other.isdigit():
            other = int(other)
        return Dt(self.dt + other)

    def __ge__(self, other):
        if isinstance(other, Dt):
            other = other.dt
        return self.dt >= other

    def to_string(self):
        return datetime.fromtimestamp(self.dt).strftime(Dt.formats['datetime'])

    def to_timestamp(self):
        return int(self.dt)

    def to_request(self):
        return self.to_timestamp() * 1000

    def to_human(self):
        return str(timedelta(seconds=self.dt))  # + ' с'

    @staticmethod
    def to_report(dt_1: int, dt_2=0):
        """Возвращаем месяц и год для сессии"""
        if isinstance(dt_1, int):
            dt_1 = Dt(dt_1)
        if isinstance(dt_2, int):
            dt_2 = Dt(dt_2)
        start = dt_1.dt
        stop = dt_2.dt
        median = (start + stop) / 2
        dt = datetime.fromtimestamp(median)
        return dt.strftime('%B %Y')



if __name__ == '__main__':
    print(Dt('2017-12-03 23:41:17.906832'))
