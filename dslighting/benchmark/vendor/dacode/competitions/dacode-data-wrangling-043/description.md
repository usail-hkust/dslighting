## About Dataset **Table: aircrafts_data** | Column Name | Data Type | Description |
| ------------- | ------------ | ----------------------------- |
| aircraft_code | character(3) | Code for the aircraft |
| model | jsonb | Aircraft model in JSON format |
| range | integer | The range of the aircraft | --- **Table: airports_data** | Column Name | Data Type | Description |
| ------------ | ------------ | ------------------------------------- |
| airport_code | character(3) | Code for the airport |
| airport_name | jsonb | Name of the airport in JSON format |
| city | jsonb | City where the airport is located |
| coordinates | point | Geographic coordinates of the airport |
| timezone | text | Timezone of the airport | --- **Table: boarding_passes** | Column Name | Data Type | Description |
| ----------- | -------------------- | ---------------- |
| ticket_no | character(13) | Ticket number |
| flight_id | integer | ID of the flight |
| boarding_no | integer | Boarding number |
| seat_no | character varying(4) | Seat number | --- **Table: bookings** | Column Name | Data Type | Description |
| ------------ | ------------------------ | ----------------------------------------- |
| book_ref | character(6) | Booking reference |
| book_date | timestamp with time zone | Booking date with timestamp and time zone |
| total_amount | numeric(10,2) | Total booking amount | --- **Table: flights** | Column Name | Data Type | Description |
| ------------------- | ------------------------ | ----------------------------------------------------- |
| flight_id | integer | Flight ID |
| flight_no | character(6) | Flight number |
| scheduled_departure | timestamp with time zone | Scheduled departure time with timestamp and time zone |
| scheduled_arrival | timestamp with time zone | Scheduled arrival time with timestamp and time zone |
| departure_airport | character(3) | Departure airport code |
| arrival_airport | character(3) | Arrival airport code |
| status | character varying(20) | Flight status |
| aircraft_code | character(3) | Aircraft code |
| actual_departure | timestamp with time zone | Actual departure time with timestamp and time zone |
| actual_arrival | timestamp with time zone | Actual arrival time with timestamp and time zone | --- **Table: seats** | Column Name | Data Type | Description |
| --------------- | --------------------- | --------------- |
| aircraft_code | character(3) | Aircraft code |
| seat_no | character varying(4) | Seat number |
| fare_conditions | character varying(10) | Fare conditions | --- **Table: ticket_flights** | Column Name | Data Type | Description |
| --------------- | --------------------- | ---------------- |
| ticket_no | character(13) | Ticket number |
| flight_id | integer | ID of the flight |
| fare_conditions | character varying(10) | Fare conditions |
| amount | numeric(10,2) | Ticket amount | --- **Table: tickets** | Column Name | Data Type | Description |
| ------------ | --------------------- | ----------------- |
| ticket_no | character(13) | Ticket number |
| book_ref | character(6) | Booking reference |
| passenger_id | character varying(20) | Passenger ID |
