# dm-csv-065

## Instruction
Retrieve the necessary data to calculate the regression line for each category, with 'days' as the independent variable.

## About Dataset
The SQL query can be described in text as follows: 1. Select the date of the order purchase.
2. Calculate the number of days since January 1, 2017, and cast it as an integer.
3. Select the product category name in English.
4. Sum the price of the products to get the total sales.
5. Use the following tables: orders, order_items, products, and product_category_name_translation.
6. Join these tables based on their respective keys: order_id, product_id, and product_category_name.
7. Filter the data to include only those orders where the purchase timestamp is between January 1, 2017, and August 29, 2018.
8. Further filter the data to include only the selected categories.
9. Group the results by the calculated day and the product category name in English.
