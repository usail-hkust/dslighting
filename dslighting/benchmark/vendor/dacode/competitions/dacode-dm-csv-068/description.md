# dm-csv-068

## Instruction
Calculate the average occupancy per aircraft.

## About Dataset
This SQL query calculates the occupancy rate of each flight based on the number of booked seats and the total seats available. Here's a step-by-step explanation: 1. **Subquery `a`**: - It selects the `aircraft_code`, `flight_id`, and counts the number of `booked_seats` for each flight by joining `boarding_passes` with `flights`. - It groups the results by `aircraft_code` and `flight_id`. 2. **Subquery `b`**: - It selects the `aircraft_code` and counts the total number of seats available for each aircraft from the `seats` table. - It groups the results by `aircraft_code`. 3. **Main Query**: - It joins the results of subqueries `a` and `b` on the `aircraft_code`. - It selects the `aircraft_code`, `flight_id`, `booked_seats`, and `total_seats`. - It calculates the average occupancy rate for each aircraft by dividing the `booked_seats` by the `total_seats`. - Finally, it groups the results by `aircraft_code`. ### Text Description The query retrieves the aircraft code, flight ID, number of booked seats, total seats, and occupancy rate for each flight. It does this by first calculating the number of booked seats per flight and the total seats per aircraft, and then combining these results to compute the occupancy rate. The final output includes the average occupancy rate for each aircraft.
