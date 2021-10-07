DROP TABLE Booking CASCADE;
DROP TABLE Trip CASCADE;
DROP TABLE Driver CASCADE;
DROP TABLE Person CASCADE;

CREATE TYPE WEEKDAY AS ENUM ('Lunedì', 'Martedì', 'Mercoledì', 'Giovedì', 'Venerdì');
CREATE TYPE DIRECTION AS ENUM ('Povo', 'NEST');

CREATE TABLE Person(
     person_id NUMERIC PRIMARY KEY NOT NULL,
     full_name TEXT NOT NULL
);

CREATE TABLE Driver(
     driver_id NUMERIC PRIMARY KEY NOT NULL REFERENCES Person(person_id) ON DELETE CASCADE,
     car_name TEXT,
     slots NUMERIC NOT NULL CHECK(slots > 0)
);

CREATE TABLE Trip(
     trip_id NUMERIC NOT NULL PRIMARY KEY,
     driver_id NUMERIC NOT NULL REFERENCES Driver(driver_id) ON DELETE CASCADE,
     suspended BOOLEAN NOT NULL DEFAULT false,
     wkday WEEKDAY NOT NULL,
     dir DIRECTION NOT NULL,
     dep_date DATE NOT NULL,
     dep_time TIME NOT NULL
);

CREATE TABLE Booking(
    booker_id NUMERIC NOT NULL REFERENCES Person(person_id) ON DELETE CASCADE,
    trip_id NUMERIC NOT NULL REFERENCES Trip(trip_id) ON DELETE CASCADE,
    paid BOOLEAN NOT NULL DEFAULT false,
    PRIMARY KEY(booker_id, trip_id)
);

CREATE TABLE Debit(
    booker_id NUMERIC NOT NULL REFERENCES Person(person_id) ON DELETE CASCADE,
    driver_id NUMERIC NOT NULL REFERENCES Driver(driver_id) ON DELETE CASCADE,
    amount NUMERIC NOT NULL DEFAULT 0 CHECK (amount > 0),
    PRIMARY KEY(booker_id, driver_id)
);