# ExpenseTracker
Personal project to track and visualize my daily expenses. Transactions are recorded in an Excel file, and a Python Plotly Dash-based web app provides insights into spending trends and aggregations. The app also pulls real-time stock data from Yahoo Finance for portfolio performance reporting.

## Dashboard overview
### General
In the top part there are two toggles:
<ul>
  <li>Investments: include the category <em>Investments</em> in the reports</li>
  <li>Show months: show the monthly breakdown in the <em>Categories by Month</em> table</li>
</ul>

To the right of the toggles, the cards display a summary of the total expenses, earnings, and balance for the selected period.

In *Categories by Month* expenses are displayed in a table organized by month and category. Additional information includes the percentage each category contributes to the total earnings and expenses for the selected period.

![image](https://github.com/user-attachments/assets/097ed648-5efd-4322-81c1-a8a9b92f2989)

In *Transactions*, a filterable list of transactions is provided.

![image](https://github.com/user-attachments/assets/3ec9105f-6495-436c-846b-07f7c9093556)

*Monthly balance* features a bar chart illustrating the difference between earnings and expenses.

![image](https://github.com/user-attachments/assets/860e8138-c65b-4a3b-b0d7-b213ce3c4b28)

*Top 15 Payees* displays a bar chart highlighting the top 15 payees by total expenses within the selected period.

![image](https://github.com/user-attachments/assets/6ad47d90-f5b1-4435-bb71-605edc09d43d)

### Car
The tab *Car* contains detailed information on car-related expenses. Categories included in this tab are all those whose "Category" is set as "Car".
<ul>
  <li>Table and pie chart: absolute and percentage amounts of each category</li>
  <li>Cards: summary measures (most recent values)</li>
  <li>Charts: fuel efficiency and cumulative mileage (historical values)</li>
</ul>

![image](https://github.com/user-attachments/assets/f6ec9d26-cb62-4bcf-98d4-ca588355e5db)

The fuel efficicency measures can be calculated if the user records its transactions in the following way:
<ul>
  <li>Memo: distance shown on the odometer when the car is re-fueled (d=xxx) and liters of fuel (v=yyy) for a full refill. With partial refills it's not possible to calculate the car efficiency and the related mesures</li>
  <li>Category: <em>Car:Fuel</em></li>
</ul>

![image](https://github.com/user-attachments/assets/ba9919d9-e145-478b-8956-c31a9cb00636)
