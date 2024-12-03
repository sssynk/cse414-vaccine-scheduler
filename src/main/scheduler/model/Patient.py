import sys
sys.path.append("../util/*")
sys.path.append("../db/*")
from util.Util import Util
from db.ConnectionManager import ConnectionManager
import pymssql
import datetime


class Patient:
    def __init__(self, username, password=None, salt=None, hash=None):
        self.username = username
        self.password = password
        self.salt = salt
        self.hash = hash

    # getters
    def get(self):
        cm = ConnectionManager()
        conn = cm.create_connection()
        cursor = conn.cursor(as_dict=True)

        get_patient_details = "SELECT Salt, Hash FROM Patients WHERE Username = %s"
        try:
            cursor.execute(get_patient_details, self.username)
            for row in cursor:
                curr_salt = row['Salt']
                curr_hash = row['Hash']
                calculated_hash = Util.generate_hash(self.password, curr_salt)
                if not curr_hash == calculated_hash:
                    # print("Incorrect password")
                    cm.close_connection()
                    return None
                else:
                    self.salt = curr_salt
                    self.hash = calculated_hash
                    cm.close_connection()
                    return self
        except pymssql.Error as e:
            raise e
        finally:
            cm.close_connection()
        return None

    def get_scheduled_appointments(self):
        cm = ConnectionManager()
        conn = cm.create_connection()
        cursor = conn.cursor(as_dict=True)

        appointments = []

        get_patient_appointments = "SELECT * FROM Appointments WHERE Patient = %s"
        try:
            cursor.execute(get_patient_appointments, (self.username))
            for row in cursor:
                appointments.append(row)
        except pymssql.Error as e:
            raise e
        finally:
            cm.close_connection()

        return appointments

    def get_available_appointments(self):
        cm = ConnectionManager()
        conn = cm.create_connection()
        cursor = conn.cursor(as_dict=True)

        # keep a list so we can return later
        avail = []

        # return all available appointments
        get_available_appointments = "SELECT * FROM Availabilities"
        try:
            cursor.execute(get_available_appointments)
            for row in cursor:
                avail.append(row)
        except pymssql.Error as e:
            raise e
        finally:
            cm.close_connection()

        # return the list of available appointments
        return avail

    def get_available_appointments_for(self, date):
        cm = ConnectionManager()
        conn = cm.create_connection()
        cursor = conn.cursor(as_dict=True)

        # keep a list so we can return later
        avail = []

        # return all available appointments
        get_available_appointments = "SELECT * FROM Availabilities"
        try:
            cursor.execute(get_available_appointments)
            date = datetime.datetime.strptime(date, '%m-%d-%Y').date()

            for row in cursor:
                # convert date to datetime object
                # the row['Time'] is in datetime.date format
                if row['Time'] == date:
                    avail.append(row)
        except pymssql.Error as e:
            raise e
        finally:
            cm.close_connection()

        # return the list of available appointments
        return avail

    def schedule_appointment(self, date, vaccine):
        cm = ConnectionManager()
        conn = cm.create_connection()
        cursor = conn.cursor(as_dict=True)

        # first, check to make sure the date is available (this will also get the caregiver)
        is_date_available = "SELECT * FROM Availabilities WHERE Time = %s"
        # second, check to make sure the vaccine has more then 0 doses left
        has_vaccine_available = "SELECT * FROM Vaccines WHERE Name = %s AND Doses > 0"
        # third, decrement the vaccine doses
        decrement_vaccine = "UPDATE Vaccines SET Doses = Doses - 1 WHERE Name = %s"
        # fourth, remove the availability with the date and caregiver name
        remove_availability = "DELETE FROM Availabilities WHERE Time = %s AND Username = %s"
        # fifth, add the appointment
        schedule_appointment_q = "INSERT INTO Appointments VALUES (%s, %s, %s, %s)"
        # sixth, grab the appointment so we can get the id
        get_appointment = "SELECT * FROM Appointments WHERE Time = %s AND Caregiver = %s"
        # we do each of these sequentially so we can catch any errors that occur (im a python guy so...)

        try:
            # Make sure the appointment is actually valid (since we can't update text in the CLI in realtime)
            cursor.execute(is_date_available, date)
            val = cursor.fetchone()

            if not val:
                return "No caregiver is available"

            caregiver_name = val['Username']

            cursor.execute(has_vaccine_available, vaccine)
            if not cursor.fetchone():
                return "Not enough available doses"

            # checks done, lets do the actual scheduling

            cursor.execute(decrement_vaccine, vaccine)
            cursor.execute(remove_availability, (date, caregiver_name))
            cursor.execute(schedule_appointment_q, (date, caregiver_name, self.username, vaccine))

            conn.commit()

            cursor.execute(get_appointment, (date, caregiver_name))
            val = cursor.fetchone()

            conn.commit()

            return "Appointment ID " + str(val['AppointmentID']) + ", Caregiver username " + caregiver_name

        except pymssql.Error as e:
            raise e
        finally:
            cm.close_connection()

        return "Please try again"

    def cancel(self, appointment_id):
        cm = ConnectionManager()
        conn = cm.create_connection()
        cursor = conn.cursor(as_dict=True)

        get_appointment = "SELECT * FROM Appointments WHERE AppointmentID = %s"
        remove_appointment = "DELETE FROM Appointments WHERE AppointmentID = %s"
        add_availability = "INSERT INTO Availabilities VALUES (%s, %s)"
        add_vaccine = "UPDATE Vaccines SET Doses = Doses + 1 WHERE Name = %s"

        try:
            cursor.execute(get_appointment, appointment_id)
            appointment = cursor.fetchone()
            if not appointment:
                return "Appointment does not exist"

            cursor.execute(remove_appointment, appointment_id)
            cursor.execute(add_availability, (appointment['Time'], appointment['Caregiver']))
            cursor.execute(add_vaccine, appointment['Vaccine'])
            conn.commit()

            return "Successfully deleted appointment"

        except pymssql.Error as e:
            raise e
        finally:
            cm.close_connection()


    def get_salt(self):
        return self.salt

    def get_hash(self):
        return self.hash

    def save_to_db(self):
        cm = ConnectionManager()
        conn = cm.create_connection()
        cursor = conn.cursor()

        add_patients = "INSERT INTO Patients VALUES (%s, %s, %s)"
        try:
            cursor.execute(add_patients, (self.username, self.salt, self.hash))
            # you must call commit() to persist your data if you don't set autocommit to True
            conn.commit()
        except pymssql.Error:
            raise
        finally:
            cm.close_connection()
