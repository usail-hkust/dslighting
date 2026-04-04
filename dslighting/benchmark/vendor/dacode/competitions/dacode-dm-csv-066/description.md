# dm-csv-066

## Instruction
For each of the top 10 cities with the most orders, retrieve the necessary data for each timestamp of the order stages.

## About Dataset
The SQL query can be described in text as follows: 1. Select the customer city, converting it to uppercase.
2. Calculate the average time between the order approval and the order purchase.
3. Calculate the average time between the order being approved and delivered to the carrier.
4. Calculate the average time between the order being delivered to the carrier and delivered to the customer.
5. Calculate the average time between the order being delivered to the customer and the estimated delivery date.
6. Use the `orders` table and join it with the `customers` table using the `customer_id`.
7. Filter the results to include only those cities that are in the list of top cities.
8. Group the results by customer city.
9. Order the results by the sum of the average times for approval, delivery to the carrier, and delivery to the customer in descending order.
