import sys
sys.path.append("../util/*")
sys.path.append("../db/*")
from util.Util import Util
from db.ConnectionManager import ConnectionManager
import pymssql


class Caregiver:
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

        get_caregiver_details = "SELECT Salt, Hash FROM Caregivers WHERE Username = %s"
        try:
            cursor.execute(get_caregiver_details, self.username)
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

        get_caregiver_appointments = "SELECT * FROM Appointments WHERE Caregiver = %s"
        try:
            cursor.execute(get_caregiver_appointments, (self.username))
            for row in cursor:
                appointments.append(row)
        except pymssql.Error as e:
            raise e
        finally:
            cm.close_connection()

        return appointments

    def get_username(self):
        return self.username

    def get_salt(self):
        return self.salt

    def get_hash(self):
        return self.hash

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
            if not cursor.fetchone():
                return "Error occurred while updating availability"

            cursor.execute(add_vaccine, appointment['Vaccine'])
            conn.commit()

            return "Successfully deleted appointment"

        except pymssql.Error as e:
            raise e
        finally:
            cm.close_connection()

    def save_to_db(self):
        cm = ConnectionManager()
        conn = cm.create_connection()
        cursor = conn.cursor()

        add_caregivers = "INSERT INTO Caregivers VALUES (%s, %s, %s)"
        try:
            cursor.execute(add_caregivers, (self.username, self.salt, self.hash))
            # you must call commit() to persist your data if you don't set autocommit to True
            conn.commit()
        except pymssql.Error:
            raise
        finally:
            cm.close_connection()

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
            for row in cursor:
                # only add to result if the date matches
                if row['Time'] == date:
                    avail.append(row)
        except pymssql.Error as e:
            raise e
        finally:
            cm.close_connection()

        # return the list of available appointments
        return avail

    # Insert availability with parameter date d
    def upload_availability(self, d):
        cm = ConnectionManager()
        conn = cm.create_connection()
        cursor = conn.cursor()

        add_availability = "INSERT INTO Availabilities VALUES (%s , %s)"
        try:
            cursor.execute(add_availability, (d, self.username))
            # you must call commit() to persist your data if you don't set autocommit to True
            conn.commit()
        except pymssql.Error:
            # print("Error occurred when updating caregiver availability")
            raise
        finally:
            cm.close_connection()
