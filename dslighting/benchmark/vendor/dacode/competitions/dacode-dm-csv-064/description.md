# dm-csv-064

## Instruction
Identify the restaurants in the dataset that have been operating since before the year 1800.

## About Dataset
### `businesses` and `new_businesses` | column | type | meaning |
| :-------------- | ------- | -------------------------------------- |
| `business` | varchar | Name of the business. |
| `year_founded` | int | Year the business was founded. |
| `category_code` | varchar | Code for the category of the business. |
| `country_code` | char | ISO 3166-1 3-letter country code. | ### `countries` | column | type | meaning |
| :------------- | ------- | ------------------------------------------------- |
| `country_code` | varchar | ISO 3166-1 3-letter country code. |
| `country` | varchar | Name of the country. |
| `continent` | varchar | Name of the continent that the country exists in. | ### `categories` | column | type | meaning |
| :-------------- | ------- | -------------------------------------- |
| `category_code` | varchar | Code for the category of the business. |
| `category` | varchar | Description of the business category. |
