from model.Vaccine import Vaccine
from model.Caregiver import Caregiver
from model.Patient import Patient
from util.Util import Util
from db.ConnectionManager import ConnectionManager
import pymssql
import datetime
import re


'''
objects to keep track of the currently logged-in user
Note: it is always true that at most one of currentCaregiver and currentPatient is not null
        since only one user can be logged-in at a time
'''
current_patient = None

current_caregiver = None


def is_strong_password(password):
    """
    Check if a password is strong
    """
    # At least 8 characters
    if len(password) < 8:
        print("Your password should include at least 8 characters!")
        return False
    
    # Check for at least one uppercase and one lowercase letter
    if not any(c.isupper() for c in password) or not any(c.islower() for c in password):
        print("Your password should include a mixture of both uppercase and lowercase letters!")
        return False

    # A mixture of letters and numbers
    if not any(c.isalnum() for c in password):
        print("Your password should include a mixture of letters and numbers!")
        return False
    
    # Inclusion of at least one special character from "!", "@", "#", "?"
    if not any(c in "!@#?" for c in password):
        print("Your password should include at least one special character from '!','@','#', '?'")
        return False
    
    # Password meets all criteria
    return True




def create_patient(tokens):
    """
    TODO: Part 1
    """
    # create_patient <username> <password>
    # check 1: the length for tokens need to be exactlyt 3 to include all information (with the operation name)
    if len(tokens) != 3:
        print("Failed to create user.")
        return
    
    username = tokens[1]
    password = tokens[2]
    # check 2: check if the username has been taken already
    if username_exists_patient(username):
        print("Username taken, try again!")
        return
    
    # check 3: check if the password is strong
    if not is_strong_password(password):
        print("Password is not strong enough. Please follow the password guidelines.")
        return
    
    salt = Util.generate_salt()
    hash = Util.generate_hash(password, salt)

    # create the patient
    patient = Patient(username, salt=salt, hash=hash)

    # save to patient information to our database
    try:
        patient.save_to_db()
    except pymssql.Error as e:
        print("Failed to create user.")
        print("Db-Error:", e)
        quit()
    except Exception as e:
        print("Failed to create user.")
        print(e)
        return
    print(f"Create user {username}")


def username_exists_patient(username):
    cm = ConnectionManager()
    conn = cm.create_connection()

    select_username = "SELECT * FROM Patients WHERE Username = %s"
    try:
        cursor = conn.cursor(as_dict=True)
        cursor.execute(select_username, username)
        # return false if the cursor is not before the first record or if there are no rows in the ResultSet.
        for row in cursor:
            return row['Username'] is not None
    except pymssql.Error as e:
        print("Error occurred when checking username")
        print("Db-Error:", e)
        quit()
    except Exception as e:
        print("Error occurred when checking username")
        print("Error:", e)
    finally:
        cm.close_connection()
    return False
        


def create_caregiver(tokens):
    # create_caregiver <username> <password>
    # check 1: the length for tokens need to be exactly 3 to include all information (with the operation name)
    if len(tokens) != 3:
        print("Failed to create user.")
        return

    username = tokens[1]
    password = tokens[2]
    # check 2: check if the username has been taken already
    if username_exists_caregiver(username):
        print("Username taken, try again!")
        return

    # check 3: check if the password is strong
    if not is_strong_password(password):
        print("Password is not strong enough. Please follow the password guidelines.")
        return


    salt = Util.generate_salt()
    hash = Util.generate_hash(password, salt)

    # create the caregiver
    caregiver = Caregiver(username, salt=salt, hash=hash)

    # save to caregiver information to our database
    try:
        caregiver.save_to_db()
    except pymssql.Error as e:
        print("Failed to create user.")
        print("Db-Error:", e)
        quit()
    except Exception as e:
        print("Failed to create user.")
        print(e)
        return
    print("Created user ", username)


def username_exists_caregiver(username):
    cm = ConnectionManager()
    conn = cm.create_connection()

    select_username = "SELECT * FROM Caregivers WHERE Username = %s"
    try:
        cursor = conn.cursor(as_dict=True)
        cursor.execute(select_username, username)
        #  returns false if the cursor is not before the first record or if there are no rows in the ResultSet.
        for row in cursor:
            return row['Username'] is not None
    except pymssql.Error as e:
        print("Error occurred when checking username")
        print("Db-Error:", e)
        quit()
    except Exception as e:
        print("Error occurred when checking username")
        print("Error:", e)
    finally:
        cm.close_connection()
    return False


def login_patient(tokens):
    """
    TODO: Part 1
    """
    # login_patient <username> <password>
    # check 1: if someone's already logged-in, they need to log out first
    global current_patient, current_caregiver
    if current_patient is not None or current_caregiver is not None:
        print("User already logged in.")
        return
    
    # check 2: the length for tokens need to be exactly 3 to include all information (with the operation name)
    if len(tokens) != 3:
        print("Login failed.")
        return
    
    username = tokens[1]
    password = tokens[2]

    patient = None
    try:
        patient = Patient(username, password=password).get()
    except pymssql.Error as e:
        print("Login failed.")
        print("Db-Error:", e)
        quit()
    except Exception as e:
        print("Login failed.")
        print("Error:", e)
        return
    
    # check if the login was successful
    if patient is None:
        print("Login failed.")
    else:
        print(f"Logged in as {username}")
        current_patient = patient


def login_caregiver(tokens):
    # login_caregiver <username> <password>
    # check 1: if someone's already logged-in, they need to log out first
    global current_caregiver, current_patient
    if current_caregiver is not None or current_patient is not None:
        print("User already logged in.")
        return

    # check 2: the length for tokens need to be exactly 3 to include all information (with the operation name)
    if len(tokens) != 3:
        print("Login failed.")
        return

    username = tokens[1]
    password = tokens[2]

    caregiver = None
    try:
        caregiver = Caregiver(username, password=password).get()
    except pymssql.Error as e:
        print("Login failed.")
        print("Db-Error:", e)
        quit()
    except Exception as e:
        print("Login failed.")
        print("Error:", e)
        return

    # check if the login was successful
    if caregiver is None:
        print("Login failed.")
    else:
        print("Logged in as: " + username)
        current_caregiver = caregiver



def is_valid_date_format(date_str):
    # Use regular expression to validate the date format
    return re.match(r"\d{2}-\d{2}-\d{4}", date_str) is not None




def search_caregiver_schedule(tokens):
    """
    TODO: Part 2
    """
    # check 1: if no user is logged-in, they need to login first
    global current_patient, current_caregiver
    if current_patient is None and current_caregiver is None:
        print("Please login first!")
        return
    
    # check 2: the length for tokens need to be exactly 2 to include all information (with the operation name)
    if len(tokens) != 2:
        print("Please try again!")
        return
    
    date_str = tokens[1]

    # Validate date format
    if not is_valid_date_format(date_str):
        print("Invalid date format. Please use the format mm-dd-yyyy.")
        return
    
    # Convert date to datetime object
    try:
        appointment_date = datetime.datetime.strptime(date_str, "%m-%d-%Y").date()
    except ValueError:
        print("Invalid date. Please enter the valid date format mm-dd-yyyy.")
        return
    
    cm = ConnectionManager()
    conn = cm.create_connection()
    cursor = conn.cursor(as_dict=True)

    try:
        # Query caregivers available for the specified date
        caregiver_query = """
            SELECT c.Username AS Caregiver_Username
            FROM Caregivers c
            LEFT JOIN Availabilities a ON c.Username = a.Username AND a.Time = %s
            WHERE a.Time IS NOT NULL
            ORDER BY c.Username
        """
        cursor.execute(caregiver_query, appointment_date)

        # Print the caregiver usernames
        print("Caregiver Username:")
        for row in cursor:
            caregiver_username = row['Caregiver_Username']
            print(caregiver_username)

        # Query vaccines and available doses for the specified date
        vaccine_query = """
            SELECT Name, Doses
            FROM Vaccines
            ORDER BY Name
        """
        cursor.execute(vaccine_query)

        # Print the vaccines and available doses
        print("\nVaccine Names and Available Doses:")
        for row in cursor:
            vaccine_name = row['Name']
            available_doses = row['Doses']
            print(f"{vaccine_name} {available_doses}")

    except pymssql.Error as e:
        print("Please try again!")
        print("Db-Error:", e)
    finally:
        cm.close_connection()

    




def reserve(tokens):
    """
    TODO: Part 2
    """
    global current_patient, current_caregiver

    # Check if a user is logged in
    if current_patient is None:
        print("Please login first!")
        return
    
    # Check if the logged-in user is a patient
    if current_caregiver is not None:
        print("Please login as a patient!")
        return
    
    # Check if the length of tokens is correct
    if len(tokens) != 3:
        print("Please try again!")
        return
    
    date_str = tokens[1]
    vaccine_name = tokens[2]

    # Validate date format
    if not is_valid_date_format(date_str):
        print("Invalid date format. Please use the format mm-dd-yyyy.")
        return

    # Convert date to datetime object
    try:
        appointment_date = datetime.datetime.strptime(date_str, "%m-%d-%Y").date()
    except ValueError:
        print("Invalid date. Please enter the valid date format mm-dd-yyyy.")
        return

    # Check caregiver availability
    caregiver_username = get_available_caregiver(appointment_date)

    if caregiver_username:
        # Check vaccine availability
        if check_vaccine_availability(vaccine_name):
            # Reserve the appointment
            appointment_id = reserve_appointment(vaccine_name, appointment_date, caregiver_username)
            print(f"Appointment ID: {appointment_id}, Caregiver username: {caregiver_username}")
        else:
            print("Not enough available doses!")
    else:
        print("No Caregiver is available!")




# Define a function to get available caregiver in selected date
def get_available_caregiver(appointment_date):
    cm = ConnectionManager()
    conn = cm.create_connection()
    cursor = conn.cursor(as_dict=True)

    try:
        # Query caregivers available for the specified date
        caregiver_query = """
            SELECT c.Username AS Caregiver_Username
            FROM Caregivers c
            LEFT JOIN Availabilities a ON c.Username = a.Username AND a.Time = %s
            WHERE a.Time IS NOT NULL
            ORDER BY c.Username
        """
        cursor.execute(caregiver_query, appointment_date)

        for row in cursor:
            return row['Caregiver_Username']
        
    except pymssql.Error as e:
        print("Please try again!")
        print("Db-Error:", e)
    finally:
        cm.close_connection()
    return None

# Define a function to check the availability of the selected vaccine
def check_vaccine_availability(vaccine_name):
    cm = ConnectionManager()
    conn = cm.create_connection()
    cursor = conn.cursor()

    try:
        vaccine_query = "SELECT Doses FROM Vaccines WHERE Name = %s"
        cursor.execute(vaccine_query, vaccine_name)

        for row in cursor:
            available_doses = row[0]
            return available_doses > 0
    
    except pymssql.Error as e:
        print("Please try again!")
        print("Db-Error:", e)
    finally:
        cm.close_connection()
    return False


# Update the table Reserve, Vaccines, Availabilities and return appointment_id from table Reserve
def reserve_appointment(vaccine_name, appointment_date, caregiver_name):
    cm = ConnectionManager()
    conn = cm.create_connection()
    cursor = conn.cursor()

    try:
        # Insert reservation into the Reserve table
        insert_reserve_query = """
            INSERT INTO Reserve (vaccine_name, appointment_date, patient_name, caregiver_name)
            VALUES (%s, %s, %s, %s)
        """
        cursor.execute(insert_reserve_query, (vaccine_name, appointment_date, current_patient.get_username(), caregiver_name))
        conn.commit()

        # Get the appointment_id of the reservation from Reserve table
        select_appointment_id_query = "SELECT SCOPE_IDENTITY()"
        cursor.execute(select_appointment_id_query)
        appointment_id = cursor.fetchone()[0]

        # Remove caregiver availability for the specified date from Availabilities
        delete_availability_query = "DELETE FROM Availabilities WHERE Time = %s AND Username = %s"
        cursor.execute(delete_availability_query, (appointment_date, caregiver_name))
        conn.commit()

        # Decrement available doses for the specified vaccine in Vaccines table
        update_vaccine_query = "UPDATE Vaccines SET Doses = Doses - 1 WHERE Name = %s"
        cursor.execute(update_vaccine_query, vaccine_name)
        conn.commit()

        return appointment_id
    
    except pymssql.Error as e:
        print("Please try again!")
        print("Db-Error:", e)
    finally:
        cm.close_connection()

    return None



def upload_availability(tokens):
    #  upload_availability <date>
    #  check 1: check if the current logged-in user is a caregiver
    global current_caregiver
    if current_caregiver is None:
        print("Please login as a caregiver first!")
        return

    # check 2: the length for tokens need to be exactly 2 to include all information (with the operation name)
    if len(tokens) != 2:
        print("Please try again!")
        return

    date = tokens[1]
    # assume input is hyphenated in the format mm-dd-yyyy
    date_tokens = date.split("-")
    month = int(date_tokens[0])
    day = int(date_tokens[1])
    year = int(date_tokens[2])
    try:
        d = datetime.datetime(year, month, day)
        current_caregiver.upload_availability(d)
    except pymssql.Error as e:
        print("Upload Availability Failed")
        print("Db-Error:", e)
        quit()
    except ValueError:
        print("Please enter a valid date!")
        return
    except Exception as e:
        print("Error occurred when uploading availability")
        print("Error:", e)
        return
    print("Availability uploaded!")


def cancel(tokens):
    """
    TODO: Extra Credit
    """
    global current_patient, current_caregiver

    # Check if a user is logged in
    if current_patient is None:
        print("Please login first!")
        return
    
    # Check if the logged-in user is a patient
    if current_caregiver is not None:
        print("Please login as a patient!")
        return
    
    # Check if the length of tokens is correct
    if len(tokens) != 2:
        print("Please try again!")
        return
    
    appointment_id = int(tokens[1])

    cm = ConnectionManager()
    conn = cm.create_connection()
    cursor = conn.cursor(as_dict=True)

    try:
        # Query to check if the appointment_id exists
        check_appointment_query = """
            SELECT *
            FROM Reserve
            WHERE appointment_id = %s AND patient_name = %s
        """
        cursor.execute(check_appointment_query, (appointment_id, current_patient.get_username()))
        appointment_data = cursor.fetchone()

        if not appointment_data:
            print("Please try again! Enter a valid appointment_id!")
            return

        # Update Vaccines table by increasing available doses
        update_vaccine_query = """
            UPDATE Vaccines
            SET Doses = Doses + 1
            WHERE Name = %s
        """
        cursor.execute(update_vaccine_query, appointment_data['vaccine_name'])

        # Update Availabilities table by adding the appointment_date and caregiver_name
        update_availabilities_query = """
            INSERT INTO Availabilities (Time, Username)
            VALUES (%s, %s)
        """
        cursor.execute(update_availabilities_query, (appointment_data['appointment_date'], appointment_data['caregiver_name']))

        # Delete the appointment from the Reserve table
        delete_appointment_query = """
            DELETE FROM Reserve
            WHERE appointment_id = %s
        """
        cursor.execute(delete_appointment_query, appointment_id)

        conn.commit()

        print("Appointment canceled successfully!")

    except Exception as e:
        print("Please try again!")
        print("Error:", e)
    finally:
        cm.close_connection()





def add_doses(tokens):
    #  add_doses <vaccine> <number>
    #  check 1: check if the current logged-in user is a caregiver
    global current_caregiver
    if current_caregiver is None:
        print("Please login as a caregiver first!")
        return

    #  check 2: the length for tokens need to be exactly 3 to include all information (with the operation name)
    if len(tokens) != 3:
        print("Please try again!")
        return

    vaccine_name = tokens[1]
    doses = int(tokens[2])
    vaccine = None
    try:
        vaccine = Vaccine(vaccine_name, doses).get()
    except pymssql.Error as e:
        print("Error occurred when adding doses")
        print("Db-Error:", e)
        quit()
    except Exception as e:
        print("Error occurred when adding doses")
        print("Error:", e)
        return

    # if the vaccine is not found in the database, add a new (vaccine, doses) entry.
    # else, update the existing entry by adding the new doses
    if vaccine is None:
        vaccine = Vaccine(vaccine_name, doses)
        try:
            vaccine.save_to_db()
        except pymssql.Error as e:
            print("Error occurred when adding doses")
            print("Db-Error:", e)
            quit()
        except Exception as e:
            print("Error occurred when adding doses")
            print("Error:", e)
            return
    else:
        # if the vaccine is not null, meaning that the vaccine already exists in our table
        try:
            vaccine.increase_available_doses(doses)
        except pymssql.Error as e:
            print("Error occurred when adding doses")
            print("Db-Error:", e)
            quit()
        except Exception as e:
            print("Error occurred when adding doses")
            print("Error:", e)
            return
    print("Doses updated!")


def show_appointments(tokens):
    '''
    TODO: Part 2
    '''
    global current_patient, current_caregiver

    # Check if a user is logged in
    if current_patient is None and current_caregiver is None:
        print("Please login first!")
        return
    
    # Check if the length of tokens is correct
    if len(tokens) != 1:
        print("Please try again!")
        return
    
    cm = ConnectionManager()
    conn = cm.create_connection()
    cursor = conn.cursor(as_dict=True)

    try:
        # Get appointments for the current user
        if current_patient:
            appointments_query = """
                SELECT appointment_id, vaccine_name, appointment_date, caregiver_name
                FROM Reserve
                WHERE patient_name = %s
                ORDER BY appointment_id
            """
            cursor.execute(appointments_query, current_patient.get_username())

            # Print patient appointments
            print("Appointment_ID Vaccine_Name Date Caregiver_Name")
            for row in cursor:
                appointment_id = row['appointment_id']
                vaccine_name = row['vaccine_name']
                appointment_date = row['appointment_date'].strftime("%m-%d-%Y")
                caregiver_name = row['caregiver_name']
                print(f"{appointment_id} {vaccine_name} {appointment_date} {caregiver_name}")
        
        elif current_caregiver:
            appointments_query = """
                SELECT appointment_id, vaccine_name, appointment_date, patient_name
                FROM Reserve
                WHERE caregiver_name = %s
                ORDER BY appointment_id
            """
            cursor.execute(appointments_query, current_caregiver.get_username())

            # Print caregiver appointments
            print("Appointment_ID Vaccine_Name Date Patient_Name")
            for row in cursor:
                appointment_id = row['appointment_id']
                vaccine_name = row['vaccine_name']
                appointment_date = row['appointment_date'].strftime("%m-%d-%Y")
                patient_name = row['patient_name']
                print(f"{appointment_id} {vaccine_name} {appointment_date} {patient_name}")

    except pymssql.Error as e:
        print("Please try again!")
        print("Db-Error:", e)
    finally:
        cm.close_connection()





def logout(tokens):
    """
    TODO: Part 2
    """
    global current_patient, current_caregiver

    # Check if a user is logged in
    if current_patient is None and current_caregiver is None:
        print("Please login first!")
        return
    
    try:
        # Logout the current user
        if current_patient:
            print("Successfully logged out!")
            current_patient = None
        elif current_caregiver:
            print("Successfully logged out!")
            current_caregiver = None

    except Exception as e:
        print("Please try again!")
        print("Error:", e)




def start():
    stop = False
    print()
    print(" *** Please enter one of the following commands *** ")
    print("> create_patient <username> <password>")  # //TODO: implement create_patient (Part 1)
    print("> create_caregiver <username> <password>")
    print("> login_patient <username> <password>")  # // TODO: implement login_patient (Part 1)
    print("> login_caregiver <username> <password>")
    print("> search_caregiver_schedule <date>")  # // TODO: implement search_caregiver_schedule (Part 2)
    print("> reserve <date> <vaccine>")  # // TODO: implement reserve (Part 2)
    print("> upload_availability <date>")
    print("> cancel <appointment_id>")  # // TODO: implement cancel (extra credit)
    print("> add_doses <vaccine> <number>")
    print("> show_appointments")  # // TODO: implement show_appointments (Part 2)
    print("> logout")  # // TODO: implement logout (Part 2)
    print("> Quit")
    print()
    while not stop:
        response = ""
        print("> ", end='')

        try:
            response = str(input())
        except ValueError:
            print("Please try again!")
            break

        #response = response.lower()
        tokens = response.split(" ")
        if len(tokens) == 0:
            ValueError("Please try again!")
            continue
        operation = tokens[0].lower()
        if operation == "create_patient":
            create_patient(tokens)
        elif operation == "create_caregiver":
            create_caregiver(tokens)
        elif operation == "login_patient":
            login_patient(tokens)
        elif operation == "login_caregiver":
            login_caregiver(tokens)
        elif operation == "search_caregiver_schedule":
            search_caregiver_schedule(tokens)
        elif operation == "reserve":
            reserve(tokens)
        elif operation == "upload_availability":
            upload_availability(tokens)
        elif operation == "cancel":
            cancel(tokens)
        elif operation == "add_doses":
            add_doses(tokens)
        elif operation == "show_appointments":
            show_appointments(tokens)
        elif operation == "logout":
            logout(tokens)
        elif operation == "quit":
            print("Bye!")
            stop = True
        else:
            print("Invalid operation name!")


if __name__ == "__main__":
    '''
    // pre-define the three types of authorized vaccines
    // note: it's a poor practice to hard-code these values, but we will do this ]
    // for the simplicity of this assignment
    // and then construct a map of vaccineName -> vaccineObject
    '''

    # start command line
    print()
    print("Welcome to the COVID-19 Vaccine Reservation Scheduling Application!")

    start()
