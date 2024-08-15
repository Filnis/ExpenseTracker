# ExpenseTracker
Personal project to track and visualize my daily expenses. Transactions are recorded in an Excel file, and a Python Plotly Dash-based web app provides insights into spending trends and aggregations. The app also pulls real-time stock data from Yahoo Finance for portfolio performance reporting.

## Dashboard overview
### General
In the top part there are two toggles:
<ul>
  <li>Investments: include the category <em>Investments</em> in the reports</li>
  <li>Show months: show the monthly breakdown in the <em>Categories by Month</em> table</li>
</ul>

On the right of the toggles the cards provide a summary of the total expenses, earnings and balance in the period selected.

In *Categories by Month* the expenses are shown in a table aggregated by month and category. Additional information include the percentage of each category compared to the total earnings and total expenses in the selected period.

![image](https://github.com/user-attachments/assets/097ed648-5efd-4322-81c1-a8a9b92f2989)

In *Transactions* there is the filterable list of transactions

![image](https://github.com/user-attachments/assets/3ec9105f-6495-436c-846b-07f7c9093556)

*Monthly balance* contains a bar chart with the difference between earnings and expenses

![image](https://github.com/user-attachments/assets/860e8138-c65b-4a3b-b0d7-b213ce3c4b28)

