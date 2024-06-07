import sys
import sqlite3
import os
from PyQt5.QtWidgets import QDialog, QMessageBox, QApplication, QMainWindow, QGroupBox, QCalendarWidget, QLabel, QVBoxLayout, QWidget, QPushButton, QComboBox, QHBoxLayout, QGridLayout, QFrame, QLineEdit
from PyQt5.QtCore import QDate, Qt, QSettings, QSize, QPoint
from PyQt5.QtGui import QColor, QPainter, QIcon, QPixmap, QIntValidator

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
    
def format_number(value):
    if value is None:
        return "0"
    formatted = f"{value:.2f}".rstrip('0').rstrip('.')
    return formatted if formatted else "0"

class WorkCalendar(QCalendarWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.work_hours = {}
        self.work_types = {}  # 근무 유형 저장
        self.holidays = self.load_holidays()
        self.load_work_hours()
        self.setNavigationBarVisible(False)  # 기본 네비게이션 바 숨기기



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
        
        # 배경색을 초기화
        painter.fillRect(rect, QColor('white'))

        # 현재 달의 날짜가 아니면 흐리게 표시
        current_month = self.selectedDate().month()
        if date.month() != current_month:
            painter.setOpacity(0.3)
        else:
            painter.setOpacity(1.0)

        # 근무 유형에 따른 배경색 설정
        if date_str in self.work_types:
            work_type = self.work_types[date_str]
            if work_type == "재택근무":
                painter.fillRect(rect, QColor(0xE6, 0xFB, 0xEA))  # 연한 연두색
            elif work_type == "연/월차":
                painter.fillRect(rect, QColor(255, 219, 204))  # 연한 주황색
            elif work_type == "오전반차":
                painter.fillRect(rect, QColor(255, 255, 181))  # 연한 노랑색
            elif work_type == "오후반차":
                painter.fillRect(rect, QColor(255, 255, 181))  # 연한 노랑색
            elif work_type == "출장":
                painter.fillRect(rect, QColor(212, 240, 240))  # 연한 파랑색
            elif work_type == "교육":
                painter.fillRect(rect, QColor(236, 213, 227))  # 연한 보라색
            elif work_type == "기타":
                painter.fillRect(rect, QColor(236, 234, 228))  # 연한 회색

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
            if date_str in self.holidays or date.dayOfWeek() in (6, 7):  # 휴일 및 주말 근무 시간은 파란 글씨로 표시
                work_hours_color = QColor('blue')
            else:
                work_hours_color = QColor('blue') if hours >= 8 else QColor('red')
            painter.setPen(work_hours_color)
            painter.drawText(rect, Qt.AlignBottom | Qt.AlignRight, f"{hours:.2f}")

        # Opacity를 원래대로 복원
        painter.setOpacity(1.0)



    def load_work_hours(self):
        try:
            conn = sqlite3.connect('work_hours.db')
            cursor = conn.cursor()
            query = load_query('Select all work hours')
            cursor.execute(query)
            records = cursor.fetchall()
            for date, start_time, end_time, work_type in records:
                start_hour = int(start_time.split(':')[0])
                end_hour = int(end_time.split(':')[0])
                start_minute = int(start_time.split(':')[1])
                end_minute = int(end_time.split(':')[1])
                hours = (end_hour + end_minute / 60) - (start_hour + start_minute / 60) - 1
                self.work_hours[date] = hours
                self.work_types[date] = work_type  # 근무 유형 저장
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
        self.work_type_combo.addItem("연/월차")
        self.work_type_combo.addItem("오전반차")
        self.work_type_combo.addItem("오후반차")
        self.work_type_combo.addItem("출장")
        self.work_type_combo.addItem("교육")
        self.work_type_combo.addItem("기타")
        self.work_type_combo.setStyleSheet("QComboBox:focus { border: 1px solid lightgray; }")

        self.start_time_combo = QComboBox(self)
        self.start_time_combo.setEditable(True)
        self.start_time_combo.setStyleSheet("QComboBox:focus { border: 1px solid lightgray; }")
        for hour in range(8, 12):  # 오전 8시부터 11시 30분까지
            for minute in (0, 30):
                self.start_time_combo.addItem(f"{hour:02}:{minute:02}")

        self.end_time_combo = QComboBox(self)
        self.end_time_combo.setEditable(True)
        self.end_time_combo.setStyleSheet("QComboBox:focus { border: 1px solid lightgray; }")
        for hour in range(13, 18):  # 오후 1시부터 5시 30분까지
            for minute in (0, 30):
                self.end_time_combo.addItem(f"{hour:02}:{minute:02}")

        self.save_button = QPushButton("근무 등록", self)
        self.save_button.clicked.connect(self.save_work_hours)
        
        self.delete_button = QPushButton("근무 삭제", self)
        self.delete_button.clicked.connect(self.delete_work_hours)
        
        self.holiday_label = QLabel("Description:")
        self.holiday_desc = QLineEdit(self)
        self.holiday_desc.setStyleSheet("QLineEdit:focus { border: 1px solid lightgray; }")
        self.add_holiday_button = QPushButton("휴일 등록", self)
        self.add_holiday_button.clicked.connect(self.add_holiday)
        
        self.remove_holiday_button = QPushButton("휴일 삭제", self)
        self.remove_holiday_button.clicked.connect(self.remove_holiday)

        self.total_hours_label = QLabel("이번 달 근무시간: 0")
        self.balance_label = QLabel("여유 시간: 0")
        self.remaining_days_label = QLabel("남은 연/월차: 0")
        self.Required_label = QLabel("이번 달 필수시간: 0")

        # 연도와 달을 선택할 수 있는 드롭다운 메뉴 추가
        self.year_combo = QComboBox(self)
        self.month_combo = QComboBox(self)

        for year in range(2000, 2101):
            self.year_combo.addItem(str(year))

        for month in range(1, 13):
            self.month_combo.addItem(f"{month:02}")

        self.year_combo.setCurrentText(str(QDate.currentDate().year()))
        self.month_combo.setCurrentIndex(QDate.currentDate().month() - 1)

        self.year_combo.currentTextChanged.connect(self.update_calendar)
        self.month_combo.currentIndexChanged.connect(self.update_calendar)

        # 이전 달, 다음 달로 이동하는 버튼 추가
        self.prev_month_button = QPushButton("<", self)
        self.prev_month_button.clicked.connect(self.show_prev_month)

        self.next_month_button = QPushButton(">", self)
        self.next_month_button.clicked.connect(self.show_next_month)

        # 현재 달로 돌아오는 버튼 추가
        self.current_month_button = QPushButton("TODAY", self)
        self.current_month_button.clicked.connect(self.show_current_month)

        # 톱니바퀴 버튼 추가
        self.settings_button = QPushButton(self)
        self.settings_button.setIcon(QIcon('static/setting_icon.png'))  # 아이콘 파일 경로 설정
        self.settings_button.clicked.connect(self.open_settings)

        # 톱니바퀴 버튼을 오른쪽 상단에 배치
        top_layout = QHBoxLayout()
        top_layout.addWidget(self.prev_month_button)
        top_layout.addWidget(self.next_month_button)
        top_layout.addWidget(self.year_combo)
        top_layout.addWidget(self.month_combo)
        top_layout.addStretch()
        top_layout.addWidget(self.current_month_button)
        top_layout.addWidget(self.settings_button)

        # 메인 레이아웃 설정
        main_layout = QVBoxLayout()
        main_layout.addLayout(top_layout)
        main_layout.addWidget(self.calendar)

        # 입력 레이아웃 설정
        input_group_box = QGroupBox("근무시간 등록/삭제")
        input_layout = QVBoxLayout()
        input_layout.addWidget(self.label)

        time_layout = QHBoxLayout()
        time_layout.addWidget(self.work_type_combo)  # 근무 유형 드롭다운 추가
        time_layout.addWidget(self.start_time_combo)
        time_layout.addWidget(self.end_time_combo)
        input_layout.addLayout(time_layout)
        input_layout.addWidget(self.save_button)
        input_layout.addWidget(self.delete_button)
        input_group_box.setLayout(input_layout)

        # 휴일 관리 레이아웃 설정
        holiday_group_box = QGroupBox("빨간 날 등록/삭제")
        holiday_layout = QHBoxLayout()
        holiday_layout.addWidget(self.holiday_label)
        holiday_layout.addWidget(self.holiday_desc)
        holiday_layout.addWidget(self.add_holiday_button)
        holiday_layout.addWidget(self.remove_holiday_button)
        holiday_group_box.setLayout(holiday_layout)

        # main_layout에 있는 정보 레이아웃을 업데이트합니다.
        info_group_box = QGroupBox("이번 달 근무 정보")
        info_layout = QGridLayout()

        info_layout.addWidget(self.Required_label, 0, 1)  # 필수근무시간 왼쪽위
        info_layout.addWidget(self.total_hours_label, 1, 1)  # 총 근무시간 왼쪽아래
        info_layout.addWidget(self.balance_label, 0, 0)  # 밸런스 오른쪽 위
        info_layout.addWidget(self.remaining_days_label, 1, 0)  # 남은 휴가일수 오른쪽 아래

        info_group_box.setLayout(info_layout)



        # 레이아웃을 메인 레이아웃에 추가
        main_layout.addWidget(input_group_box)
        main_layout.addWidget(holiday_group_box)
        main_layout.addWidget(info_group_box)

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

  

        self.calendar.clicked[QDate].connect(self.show_date)
        self.calendar.currentPageChanged.connect(self.on_page_changed)  # 달력 페이지가 변경될 때 on_page_changed 호출

        self.show_date(self.calendar.selectedDate())
        self.load_remaining_leave()


    def open_settings(self):
        settings_dialog = SettingsDialog(self)
        settings_dialog.exec_()

    def show_prev_month(self):
        current_date = self.calendar.selectedDate()
        prev_month_date = current_date.addMonths(-1)
        self.year_combo.setCurrentText(str(prev_month_date.year()))
        self.month_combo.setCurrentIndex(prev_month_date.month() - 1)
        self.calendar.setSelectedDate(prev_month_date)
        self.calendar.showSelectedDate()
        self.update_calendar()

    def show_next_month(self):
        current_date = self.calendar.selectedDate()
        next_month_date = current_date.addMonths(1)
        self.year_combo.setCurrentText(str(next_month_date.year()))
        self.month_combo.setCurrentIndex(next_month_date.month() - 1)
        self.calendar.setSelectedDate(next_month_date)
        self.calendar.showSelectedDate()
        self.update_calendar()

    def update_calendar(self):
        year = int(self.year_combo.currentText())
        month = self.month_combo.currentIndex() + 1
        new_date = QDate(year, month, 1)
        self.calendar.setSelectedDate(new_date)
        self.calendar.showSelectedDate()
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
        db_path = 'work_hours.db'
        db_exists = os.path.exists(db_path)
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        if not db_exists:
            queries = [
                'Create tables',
                'Create holidays table',
                'Create settings table'
            ]
            for query_name in queries:
                query = load_query(query_name)
                self.cursor.execute(query)
            self.conn.commit()

    def show_date(self, date):
        formatted_date = date.toString("yyyy-MM-dd dddd")
        self.label.setText(formatted_date)

        start_time, end_time, work_type = self.load_work_hours(date)
        self.start_time_combo.setCurrentText(start_time if start_time else "08:00")
        self.end_time_combo.setCurrentText(end_time if end_time else "17:00")
        self.work_type_combo.setCurrentText(work_type if work_type else "일반근무")

        holiday_desc = self.load_holiday_description(date)
        self.holiday_desc.setText(holiday_desc if holiday_desc else "")

        self.update_info()  # 날짜를 표시할 때마다 정보 업데이트

    def load_holiday_description(self, date):
        date_str = date.toString("yyyy-MM-dd")
        query = load_query('Select holiday description for a specific date')
        self.cursor.execute(query, (date_str,))
        result = self.cursor.fetchone()
        return result[0] if result else None




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
            previous_work_type = self.load_work_hours(self.calendar.selectedDate())[2]
            self.adjust_remaining_leave(previous_work_type, undo=False)  # 이전 근무 타입에 따른 남은 휴가 복원

            query = load_query('Insert or replace work hours')
            self.cursor.execute(query, (date, start_time, end_time, work_type))
            self.conn.commit()
            self.calendar.load_work_hours()
            self.calendar.updateCells()

            # balance와 모든 근무일에 근무시간이 등록되었는지 확인
            balance, all_days_worked = self.update_balance_and_leave()
            if all_days_worked and balance >= 0 and date not in self.calendar.holidays:
                self.adjust_remaining_leave("increment")

            self.label.setText(f"Saved: {date} - {work_type} - {start_time} to {end_time}")

            self.adjust_remaining_leave(work_type, undo=True)  # 새 근무 타입에 따른 남은 휴가 반영

            self.update_info()


    def delete_work_hours(self):
        date = self.calendar.selectedDate().toString("yyyy-MM-dd")
        previous_work_type = self.load_work_hours(self.calendar.selectedDate())[2]
        if date:
            # balance와 모든 근무일에 근무시간이 등록되었는지 확인
            balance, all_days_worked = self.update_balance_and_leave()
            if all_days_worked and balance >= 0 and date not in self.calendar.holidays:
                self.adjust_remaining_leave("decrement")

            query = load_query('Delete work hours')
            self.cursor.execute(query, (date,))
            self.conn.commit()
            self.calendar.load_work_hours()
            self.calendar.work_hours.pop(date, None)  # 즉시 삭제 반영
            self.calendar.work_types.pop(date, None)  # 근무 유형도 삭제 반영
            self.calendar.updateCells()  # UI 즉시 갱신
            self.label.setText(f"Deleted work hours for {date}")

            self.adjust_remaining_leave(previous_work_type, undo=False)  # 이전 근무 타입에 따른 남은 휴가 복원

            self.update_info()


    def adjust_remaining_leave(self, work_type, undo=False):
        current_leave = float(self.remaining_days_label.text().split(":")[1].strip())
        adjustment = 0
        if work_type == "연/월차":
            adjustment = 1
        elif work_type == "오전반차" or work_type == "오후반차":
            adjustment = 0.5
        elif work_type == "increment":
            adjustment = 1
        elif work_type == "decrement":
            adjustment = -1

        if undo:
            adjustment = -adjustment

        new_leave = current_leave + adjustment
        self.update_remaining_leave(new_leave)


    def update_balance_and_leave(self):
        selected_date = self.calendar.selectedDate()
        year = selected_date.year()
        month = selected_date.month()

        current_month_hours = {
            date: hours for date, hours in self.calendar.work_hours.items()
            if QDate.fromString(date, "yyyy-MM-dd").year() == year and QDate.fromString(date, "yyyy-MM-dd").month() == month
        }

        total_hours = sum(current_month_hours.values())
        work_days = self.calendar.get_work_days_in_current_month(year, month)

        # balance 계산
        balance = 0
        for date, hours in current_month_hours.items():
            qdate = QDate.fromString(date, "yyyy-MM-dd")
            if date in self.calendar.holidays or qdate.dayOfWeek() in (6, 7):  # 휴일 및 주말 근무 시간
                balance += hours
            else:
                balance += (hours - 8) if hours != 0 else -8

        # 근무 시간이 등록된 근무일 수 계산
        workdays_with_hours = len([date for date in current_month_hours if QDate.fromString(date, "yyyy-MM-dd").dayOfWeek() not in (Qt.Saturday, Qt.Sunday) and date not in self.calendar.holidays])

        all_days_worked = workdays_with_hours == work_days

        return balance, all_days_worked

    def load_work_hours(self, date):
        date_str = date.toString("yyyy-MM-dd")  # QDate 객체를 문자열로 변환
        query = load_query('Select work hours for a specific date')
        self.cursor.execute(query, (date_str,))
        result = self.cursor.fetchone()
        return result if result else (None, None, None)
    
    def add_holiday(self):
        date = self.calendar.selectedDate().toString("yyyy-MM-dd")
        description = self.holiday_desc.text() or "Holiday"  # 설명 필드가 비어있을 경우 기본값 설정
        
        if date:
            # 현재 상태에서 balance와 모든 근무일에 근무시간이 등록되었는지 확인
            previous_balance, was_all_days_worked = self.update_balance_and_leave()

            query = load_query('Insert or replace holiday')
            self.cursor.execute(query, (date, description))
            self.conn.commit()
            self.calendar.holidays = self.calendar.load_holidays()
            self.calendar.updateCells()
            self.label.setText(f"Added holiday: {description} on {date}")

            # 휴일 추가 후 상태에서 balance와 모든 근무일에 근무시간이 등록되었는지 확인
            current_balance, all_days_worked = self.update_balance_and_leave()
            if all_days_worked and current_balance >= 0 and not was_all_days_worked:
                self.adjust_remaining_leave("increment")  # 남은 휴가일 수 증가

            self.update_info()  # add_holiday 후에 정보 업데이트

    def remove_holiday(self):
        date = self.calendar.selectedDate().toString("yyyy-MM-dd")
        
        if date:
            # 현재 상태에서 balance와 모든 근무일에 근무시간이 등록되었는지 확인
            previous_balance, was_all_days_worked = self.update_balance_and_leave()

            query = load_query('Delete holiday')
            self.cursor.execute(query, (date,))
            self.conn.commit()
            self.calendar.holidays = self.calendar.load_holidays()
            self.calendar.updateCells()
            self.label.setText(f"Removed holiday on {date}")

            # 휴일 삭제 후 상태에서 balance와 모든 근무일에 근무시간이 등록되었는지 확인
            current_balance, all_days_worked = self.update_balance_and_leave()
            if not all_days_worked and was_all_days_worked and previous_balance >= 0:
                self.adjust_remaining_leave("decrement")  # 남은 휴가일 수 감소

            self.update_info()  # remove_holiday 후에 정보 업데이트

    def format_number(value):
        return f"{value:.2f}".rstrip('0').rstrip('.') if '.' in f"{value:.2f}" else f"{value:.2f}"



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
        work_days = self.calendar.get_work_days_in_current_month(year, month)

        # balance 계산 수정
        balance = 0
        for date, hours in current_month_hours.items():
            qdate = QDate.fromString(date, "yyyy-MM-dd")
            if date in self.calendar.holidays or qdate.dayOfWeek() in (6, 7):  # 휴일 및 주말 근무 시간
                balance += hours
            else:
                balance += (hours - 8) if hours != 0 else -8

        required = work_days * 8

        # balance 색상 설정
        balance_text = f"{balance:.2f}" if balance % 1 != 0 else f"{balance:.0f}"
        if balance < 0:
            self.balance_label.setText(f"여유 시간: <span style='color:red'>{balance_text}</span>")
        else:
            self.balance_label.setText(f"여유 시간: <span style='color:blue'>{balance_text}</span>")

        self.total_hours_label.setText(f"이번 달 근무시간: {total_hours:.2f}" if total_hours % 1 != 0 else f"이번 달 근무시간: {total_hours:.0f}")
        self.Required_label.setText(f"이번 달 필수시간: {required:.2f}" if required % 1 != 0 else f"이번 달 필수시간: {required:.0f}")
        self.remaining_days_label.setText(f"남은 연/월차: {format_number(self.load_remaining_leave())}")


    def load_remaining_leave(self):
        try:
            conn = sqlite3.connect('work_hours.db')
            cursor = conn.cursor()
            query = load_query('Select remaining leave')
            cursor.execute(query)
            result = cursor.fetchone()
            conn.close()
            if result:
                return float(result[0])
            else:
                return 0.0
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return 0.0


    def update_remaining_leave(self, remaining_leave):
        remaining_leave = float(remaining_leave)  # 문자열을 float으로 변환
        self.remaining_days_label.setText(f"남은 연/월차: {format_number(remaining_leave)}")
        try:
            conn = sqlite3.connect('work_hours.db')
            cursor = conn.cursor()
            query = load_query('Insert or replace remaining leave')
            cursor.execute(query, (remaining_leave,))
            conn.commit()
            conn.close()
        except sqlite3.Error as e:
            print(f"Database error: {e}")


    def closeEvent(self, event):
        self.save_window_settings()
        self.conn.close()
        event.accept()


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
    
class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent  # 부모 윈도우 저장

        self.setWindowTitle("Settings")

        main_layout = QVBoxLayout()

        # 남은 휴가일 수 입력 그룹박스
        leave_group_box = QGroupBox("남은 휴가일 수 설정")
        leave_layout = QVBoxLayout()
        self.leave_label = QLabel("남은 휴가일 수:")
        self.remaining_leave_input = QLineEdit()
        self.remaining_leave_input.setValidator(QIntValidator(0, 365))  # 휴가일 수의 유효 범위 설정
        self.remaining_leave_input.setStyleSheet("QLineEdit:focus { border: 1px solid lightgray; }")
        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self.save_settings)

        leave_layout.addWidget(self.leave_label)
        leave_layout.addWidget(self.remaining_leave_input)
        leave_layout.addWidget(self.save_button)
        leave_group_box.setLayout(leave_layout)


        # 데이터 리셋 그룹박스
        reset_group_box = QGroupBox("데이터 관리")
        reset_layout = QVBoxLayout()
        self.reset_button = QPushButton("Data Reset")
        self.reset_button.setStyleSheet("background-color: red; color: white;")
        self.reset_button.clicked.connect(self.confirm_reset)
        reset_layout.addWidget(self.reset_button)
        reset_group_box.setLayout(reset_layout)

        main_layout.addWidget(leave_group_box)
        main_layout.addWidget(reset_group_box)

        self.setLayout(main_layout)

    def save_settings(self):
        # 설정 저장 로직을 여기에 추가
        remaining_leave = self.remaining_leave_input.text()
        try:
            remaining_leave = float(remaining_leave)  # 문자열을 float으로 변환
            conn = sqlite3.connect('work_hours.db')
            cursor = conn.cursor()
            query = load_query('Insert or replace remaining leave')
            cursor.execute(query, (remaining_leave,))
            conn.commit()
            conn.close()
            print(f"Remaining leave days saved: {remaining_leave}")

            # 부모 윈도우의 remaining leave 업데이트
            self.parent.update_remaining_leave(remaining_leave)

        except ValueError as e:
            print(f"Value error: {e}")
        except sqlite3.Error as e:
            print(f"Database error: {e}")

        self.accept()

    def confirm_reset(self):
        reply = QMessageBox.question(self, 'Data Reset Confirmation',
                                     '정말로 데이터를 리셋하시겠습니까? 리셋된 데이터는 복구할 수 없습니다.',
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            self.reset_data()

    def reset_data(self):
        # 데이터베이스 초기화 로직
        conn = sqlite3.connect('work_hours.db')
        cursor = conn.cursor()

        # Drop tables
        cursor.execute(load_query('Drop work_hours table'))
        cursor.execute(load_query('Drop holidays table'))
        cursor.execute("DROP TABLE IF EXISTS settings")

        # Recreate tables
        cursor.execute(load_query('Create tables'))
        cursor.execute(load_query('Create holidays table'))
        cursor.execute(load_query('Create settings table'))

        conn.commit()
        conn.close()
        print("Data has been reset.")

        # 부모 윈도우의 달력 갱신
        self.parent.calendar.work_hours.clear()
        self.parent.calendar.holidays.clear()
        self.parent.calendar.work_types.clear()
        self.parent.calendar.updateCells()

        # 남은 휴가일 수 초기화
        self.parent.update_remaining_leave(0.0)

        self.accept()





# WorkHoursManager 클래스에서 SettingsDialog를 열 때 부모를 전달
def open_settings(self):
    settings_dialog = SettingsDialog(self)
    settings_dialog.exec_()

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



if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # 고해상도 아이콘 설정
    icon = QIcon()
    icon.addPixmap(QPixmap('static/app_icon.png'), QIcon.Normal, QIcon.On)
    app.setWindowIcon(icon)

    window = WorkHoursManager()
    window.show()
    sys.exit(app.exec_())
