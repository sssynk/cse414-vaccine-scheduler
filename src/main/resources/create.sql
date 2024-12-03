CREATE TABLE Caregivers (
    Username varchar(255),
    Salt BINARY(16),
    Hash BINARY(16),
    PRIMARY KEY (Username)
);

CREATE TABLE Availabilities (
    Time date,
    Username varchar(255) NOT NULL,
    FOREIGN KEY (Username) REFERENCES Caregivers(Username),
    PRIMARY KEY (Time, Username)
);

CREATE TABLE Vaccines (
    Name varchar(255),
    Doses int,
    PRIMARY KEY (Name)
);

CREATE TABLE Appointments (
    AppointmentID int NOT NULL IDENTITY(1,1),
    Time date NOT NULL,
    Caregiver varchar(255) NOT NULL,
    Patient varchar(255) NOT NULL,
    Vaccine varchar(255) NOT NULL,
    FOREIGN KEY (Caregiver) REFERENCES Caregivers(Username),
    FOREIGN KEY (Patient) REFERENCES Patients(Username),
    FOREIGN KEY (Vaccine) REFERENCES Vaccines(Name),
    PRIMARY KEY (AppointmentID)
);

CREATE TABLE Patients (
    Username varchar(255),
    Salt BINARY(16),
    Hash BINARY(16),
    PRIMARY KEY (Username)
);
