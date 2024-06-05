import sys
import sqlite3
from PyQt5.QtWidgets import QApplication, QMainWindow, QCalendarWidget, QLabel, QVBoxLayout, QWidget, QPushButton, QComboBox, QHBoxLayout, QGridLayout, QFrame, QLineEdit
from PyQt5.QtCore import QDate, Qt, QSettings, QSize, QPoint
from PyQt5.QtGui import QColor, QPainter

def load_query(query_name):
    with open('queries.sql', 'r') as file:
        queries = file.read().split(';')
        query_dict = {}
        for query in queries:
            if query.strip():
                lines = query.strip().split('\n')
                name = lines[0].strip().lstrip('-- ')
                query_dict[name] = '\n'.join(lines[1:]).strip()
        return query_dict[query_name]

class WorkCalendar(QCalendarWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.work_hours = {}
        self.holidays = self.load_holidays()
        self.load_work_hours()

    def get_work_days_in_current_month(self, year, month):
        first_day = QDate(year, month, 1)
        last_day = QDate(year, month, first_day.daysInMonth())
        work_days = 0

        for day in range(first_day.day(), last_day.day() + 1):
            date = QDate(first_day.year(), first_day.month(), day)
            date_str = date.toString("yyyy-MM-dd")

            if date.dayOfWeek() not in (Qt.Saturday, Qt.Sunday) and date_str not in self.holidays:
                work_days += 1

        return work_days

    def paintCell(self, painter, rect, date):
        super().paintCell(painter, rect, date)
        date_str = date.toString("yyyy-MM-dd")
        
        # 기본 글씨 색상을 검정색으로 설정
        painter.setPen(QColor('black'))

        # 공휴일 또는 주말인 경우 글씨를 빨간색으로 설정
        is_holiday_or_weekend = date_str in self.holidays or date.dayOfWeek() in (6, 7)
        if is_holiday_or_weekend:
            painter.setPen(QColor('red'))

        # 날짜를 중앙에 그립니다.
        painter.drawText(rect, Qt.AlignCenter, str(date.day()))

        # 근무 시간이 있는 경우, 근무 시간을 별도로 표시
        if date_str in self.work_hours:
            hours = self.work_hours[date_str]
            work_hours_color = QColor('blue') if hours >= 8 else QColor('red')
            painter.setPen(work_hours_color)
            painter.drawText(rect, Qt.AlignBottom | Qt.AlignRight, f"{hours}h")

    def load_work_hours(self):
        try:
            conn = sqlite3.connect('work_hours.db')
            cursor = conn.cursor()
            query = load_query('Select all work hours')
            cursor.execute(query)
            records = cursor.fetchall()
            for date, start_time, end_time in records:
                start_hour = int(start_time.split(':')[0])
                end_hour = int(end_time.split(':')[0])
                hours = end_hour - start_hour - 1
                self.work_hours[date] = hours
            conn.close()
        except sqlite3.Error as e:
            print(f"Database error: {e}")

    def load_holidays(self):
        holidays = set()
        try:
            conn = sqlite3.connect('work_hours.db')
            cursor = conn.cursor()
            query = load_query('Select all holidays')
            cursor.execute(query)
            records = cursor.fetchall()
            for record in records:
                holidays.add(record[0])
            conn.close()
        except sqlite3.Error as e:
            print(f"Database error: {e}")
        return holidays
class WorkHoursManager(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Work Hours Manager")

        self.load_window_settings()

        self.init_db()

        self.calendar = WorkCalendar(self)
        self.calendar.setGridVisible(True)

        self.label = QLabel(self)
        self.label.setText("Select a date")

        self.work_type_combo = QComboBox(self)  # 근무 유형 드롭다운 추가
        self.work_type_combo.addItem("일반근무")
        self.work_type_combo.addItem("재택근무")

        self.start_time_combo = QComboBox(self)
        self.end_time_combo = QComboBox(self)

        # 시작 시간: 오전만, 30분 단위
        self.start_time_combo.setEditable(True)
        for hour in range(8, 12):  # 오전 8시부터 11시 30분까지
            for minute in (0, 30):
                self.start_time_combo.addItem(f"{hour:02}:{minute:02}")

        # 끝 시간: 오후만, 30분 단위
        self.end_time_combo.setEditable(True)
        for hour in range(13, 18):  # 오후 1시부터 5시 30분까지
            for minute in (0, 30):
                self.end_time_combo.addItem(f"{hour:02}:{minute:02}")

        self.save_button = QPushButton("Save", self)
        self.save_button.clicked.connect(self.save_work_hours)
        
        self.delete_button = QPushButton("Delete", self)
        self.delete_button.clicked.connect(self.delete_work_hours)
        
        self.holiday_label = QLabel("Holiday Description:")
        self.holiday_desc = QLineEdit(self)
        self.add_holiday_button = QPushButton("Add Holiday", self)
        self.add_holiday_button.clicked.connect(self.add_holiday)
        
        self.remove_holiday_button = QPushButton("Remove Holiday", self)
        self.remove_holiday_button.clicked.connect(self.remove_holiday)

        self.total_hours_label = QLabel("Total Hours: 0")
        self.valance_label = QLabel("Valance: 0")
        self.remaining_days_label = QLabel("Remaining Leave: 0")
        self.Required_label = QLabel("Required: 0")

        # 현재 달로 돌아오는 버튼 추가
        self.current_month_button = QPushButton("TODAY", self)
        self.current_month_button.clicked.connect(self.show_current_month)

        main_layout = QVBoxLayout()
        top_layout = QHBoxLayout()
        top_layout.addWidget(QLabel(f"{QDate.currentDate().toString('MMMM yyyy')}", self))
        top_layout.addWidget(self.current_month_button)  # 버튼 추가
        top_layout.addStretch()

        main_layout.addLayout(top_layout)
        main_layout.addWidget(self.calendar)

        input_layout = QVBoxLayout()
        input_layout.addWidget(self.label)
        
        time_layout = QHBoxLayout()
        time_layout.addWidget(self.work_type_combo)  # 근무 유형 드롭다운 추가
        time_layout.addWidget(self.start_time_combo)
        time_layout.addWidget(self.end_time_combo)
        input_layout.addLayout(time_layout)
        input_layout.addWidget(self.save_button)
        input_layout.addWidget(self.delete_button)
        
        holiday_layout = QHBoxLayout()
        holiday_layout.addWidget(self.holiday_label)
        holiday_layout.addWidget(self.holiday_desc)
        input_layout.addLayout(holiday_layout)
        input_layout.addWidget(self.add_holiday_button)
        input_layout.addWidget(self.remove_holiday_button)
        
        main_layout.addLayout(input_layout)

        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        main_layout.addWidget(line)

        info_layout = QVBoxLayout()
        info_layout.addWidget(self.total_hours_label)
        info_layout.addWidget(self.remaining_days_label)
        info_layout.addWidget(self.valance_label)
        info_layout.addWidget(self.Required_label)
        
        main_layout.addLayout(info_layout)

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

        self.calendar.clicked[QDate].connect(self.show_date)
        self.calendar.currentPageChanged.connect(self.on_page_changed)  # 달력 페이지가 변경될 때 on_page_changed 호출

        self.show_date(self.calendar.selectedDate())
        self.update_info()


    def show_current_month(self):
        self.calendar.setSelectedDate(QDate.currentDate())
        self.calendar.showSelectedDate()
        self.update_info()  # 현재 달로 이동 시 정보 업데이트

    def load_window_settings(self):
        settings = QSettings('MyCompany', 'WorkHoursManager')
        self.resize(settings.value('windowSize', QSize(600, 400)))
        self.move(settings.value('windowPos', QPoint(100, 100)))

    def save_window_settings(self):
        settings = QSettings('MyCompany', 'WorkHoursManager')
        settings.setValue('windowSize', self.size())
        settings.setValue('windowPos', self.pos())

    def init_db(self):
        self.conn = sqlite3.connect('work_hours.db')
        self.cursor = self.conn.cursor()
        queries = [
            'Create tables',
            'Create holidays table',  # holidays 테이블 생성 쿼리 추가
        ]
        for query_name in queries:
            query = load_query(query_name)
            self.cursor.execute(query)
        self.conn.commit()

    def show_date(self, date):
        self.label.setText(date.toString())
        self.work_type_combo.setCurrentText("일반근무")
        self.start_time_combo.setCurrentText("08:00")
        self.end_time_combo.setCurrentText("17:00")

        start_time, end_time = self.load_work_hours(date)
        self.start_time_combo.setCurrentText(start_time if start_time else "08:00")
        self.end_time_combo.setCurrentText(end_time if end_time else "17:00")
        
        self.update_info()  # 날짜를 표시할 때마다 정보 업데이트

    def on_page_changed(self):
        selected_date = self.calendar.selectedDate()
        year = selected_date.year()
        month = self.calendar.monthShown()
        
        first_day_of_month = QDate(year, month, 1)
        self.calendar.setSelectedDate(first_day_of_month)
        self.update_info()  # 페이지가 변경될 때 정보 업데이트

    def save_work_hours(self):
        date = self.calendar.selectedDate().toString("yyyy-MM-dd")
        work_type = self.work_type_combo.currentText()
        start_time = self.start_time_combo.currentText()
        end_time = self.end_time_combo.currentText()
        if date and start_time and end_time:
            query = load_query('Insert or replace work hours')
            self.cursor.execute(query, (date, start_time, end_time, work_type))
            self.conn.commit()
            self.calendar.load_work_hours()
            self.calendar.updateCells()
            self.label.setText(f"Saved: {date} - {work_type} - {start_time} to {end_time}")
            self.update_info()

    def delete_work_hours(self):
        date = self.calendar.selectedDate().toString("yyyy-MM-dd")
        if date:
            query = load_query('Delete work hours')
            self.cursor.execute(query, (date,))
            self.conn.commit()
            self.calendar.load_work_hours()
            self.calendar.work_hours.pop(date, None)  # 즉시 삭제 반영
            self.calendar.updateCells()  # UI 즉시 갱신
            self.label.setText(f"Deleted work hours for {date}")
            self.update_info()

    def load_work_hours(self, date):
        date_str = date.toString("yyyy-MM-dd")  # QDate 객체를 문자열로 변환
        query = load_query('Select work hours for a specific date')
        self.cursor.execute(query, (date_str,))
        result = self.cursor.fetchone()
        return result if result else (None, None)

    def add_holiday(self):
        date = self.calendar.selectedDate().toString("yyyy-MM-dd")
        description = self.holiday_desc.text() or "Holiday"  # 설명 필드가 비어있을 경우 기본값 설정
        if date:
            query = load_query('Insert or ignore holiday')
            self.cursor.execute(query, (date, description))
            self.conn.commit()
            self.calendar.holidays = self.calendar.load_holidays()
            self.calendar.updateCells()
            self.label.setText(f"Added holiday: {description} on {date}")
            self.update_info()  # add_holiday 후에 정보 업데이트


    def remove_holiday(self):
        date = self.calendar.selectedDate().toString("yyyy-MM-dd")
        if date:
            query = load_query('Delete holiday')
            self.cursor.execute(query, (date,))
            self.conn.commit()
            self.calendar.holidays = self.calendar.load_holidays()
            self.calendar.updateCells()
            self.label.setText(f"Removed holiday on {date}")
            self.update_info()  # remove_holiday 후에 정보 업데이트


    def update_info(self):
        selected_date = self.calendar.selectedDate()
        year = selected_date.year()
        month = selected_date.month()

        # 현재 달에 해당하는 work_hours 필터링
        current_month_hours = {
            date: hours for date, hours in self.calendar.work_hours.items()
            if QDate.fromString(date, "yyyy-MM-dd").year() == year and QDate.fromString(date, "yyyy-MM-dd").month() == month
        }
        
        total_hours = sum(current_month_hours.values())
        valance = total_hours - len(current_month_hours) * 8
        required = self.calendar.get_work_days_in_current_month(year, month) * 8

        self.total_hours_label.setText(f"Total Hours: {total_hours}")
        self.valance_label.setText(f"Valance: {valance}")
        self.Required_label.setText(f"Required: {required}")
        # 나중에 연월차 관련 정보 업데이트
        # self.remaining_days_label.setText(f"Remaining Leave: {remaining_leave}")

    def closeEvent(self, event):
        self.save_window_settings()
        self.conn.close()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = WorkHoursManager()
    window.show()
    sys.exit(app.exec_())
