import dash
from dash import dcc, html, Input, Output, callback
import dash_bootstrap_components as dbc
from dash_bootstrap_templates import load_figure_template
import pandas as pd
from decimal import *
from pathlib import Path
from support_functions import get_table, float2dec, create_date_table2
import yfinance as yf
from datetime import datetime

## Load data
#The path to the expense file is written in configuration.txt 
filepath = Path("__file__").parent / "configuration.txt"
f = open(filepath, "r")
file_path = f.read()
f.close()

# load excel tables into dataframes
transactions = get_table(file_path, 'Transactions', 'Transactions')
payees = get_table(file_path, 'Payees', 'Payees')
accounts = get_table(file_path, 'Accounts', 'Accounts')
categories = get_table(file_path, 'Categories', 'Categories')

# Add year and month columns to transactions
transactions['Year'] = transactions['Date'].dt.strftime('%Y')
transactions['Year'] = pd.to_numeric(transactions['Year'], errors='coerce')

transactions['Month'] = transactions['Date'].dt.strftime('%m')
transactions['Month'] = pd.to_numeric(transactions['Month'], errors='coerce')

#Amount should be decimal
transactions['Amount'] = (transactions['Amount'].map(float2dec) * float2dec(1)).map(float2dec)
accounts['Start balance'] = (accounts['Start balance'].map(float2dec) * float2dec(1)).map(float2dec)

#Split Category in main and sub
transactions[['Cat', 'SubCat']] = transactions['Category'].str.split(":", expand = True)

# get year list
year_list = sorted([*{*transactions['Year']}])

##Load investment data
#create date table
start_date = transactions['Date'].min()
end_date = datetime.now()
date_table = create_date_table2(start_date, end_date)

# filter transactions only with sub-category stocks
tra_portfolio = transactions.loc[transactions['SubCat']=='Stocks', ['Date','Amount','Memo']]
tra_portfolio[['Ticker', 'Qty']] = tra_portfolio['Memo'].str.split(":", expand = True)
tra_portfolio['Qty'] = pd.to_numeric(tra_portfolio['Qty'], errors='coerce')
tra_portfolio.loc[tra_portfolio['Amount'] > 0, 'Qty'] = -tra_portfolio['Qty']

#merge date table with portfolio
date_table_portfolio = tra_portfolio.copy()
date_table_portfolio['Amount'] = pd.to_numeric(date_table_portfolio['Amount'])

#Get the stock list from the tickers
stockList = date_table_portfolio['Ticker'].dropna().unique()
stocks = ' '.join(stockList)

#download stock data
stocks_data = yf.download(stocks, start_date, end_date).Close.reset_index(drop=False).melt(id_vars='Date').sort_values(['Date'], ascending=[True])

# add stock value on every date
date_table_portfolio = date_table_portfolio.sort_values(by='Date', ascending=True)
date_table_portfolio['cumsum_amount'] = date_table_portfolio.groupby(['Ticker'])['Amount'].cumsum()
date_table_portfolio['cumsum_qty'] = date_table_portfolio.groupby(['Ticker'])['Qty'].cumsum()

datetable_portfolio = pd.DataFrame()
pd.options.mode.copy_on_write = "warn"
if len(stockList)==1:
    stocks_data['Ticker'] = stockList[0]
    
# loop every stock
loop_start = True
for ticker in stockList:
    temp_df = date_table_portfolio.loc[date_table_portfolio['Ticker']==ticker,:]
    # fill down days with no transactions
    temp_df = pd.merge(date_table, temp_df, left_on="Date", right_on="Date", how="left").sort_values(by='Date', ascending=True)
    temp_df['cumsum_qty'] = temp_df['cumsum_qty'].ffill(axis = 0)
    temp_df['cumsum_amount'] = temp_df['cumsum_amount'].ffill(axis = 0)
    temp_df['Ticker'] = temp_df['Ticker'].ffill(axis = 0)
    temp_df = temp_df[temp_df['cumsum_qty']>0]

    # fill down stocks value for days with closed stock exchanges
    temp_df = pd.merge(temp_df, stocks_data, left_on=["Date","Ticker"], right_on=["Date","Ticker"], how="left").sort_values(by='Date', ascending=True)
    temp_df.loc[:,'value'] = temp_df['value'].ffill(axis = 0)
    temp_df.loc[:,'cumsum_value'] = temp_df['cumsum_qty']*temp_df['value']
    temp_df.loc[:,'performance'] = ""

    if loop_start :
        datetable_portfolio = temp_df.copy()
    else: 
        datetable_portfolio = pd.concat([datetable_portfolio, temp_df], ignore_index=True)
    
    loop_start = False

# add performance based on total expens evs total actual value
datetable_portfolio.loc[datetable_portfolio['cumsum_qty']>0,'performance'] = \
    (datetable_portfolio['cumsum_value'] - abs(datetable_portfolio['cumsum_amount'])) / abs(datetable_portfolio['cumsum_amount'])*100

# total performance
total_performance = datetable_portfolio.groupby(['Date','Day_num']).sum().reset_index().sort_values(['Date'], ascending=[True])
total_performance['performance'] = \
    (total_performance['cumsum_value'] - abs(total_performance['cumsum_amount'])) / abs(total_performance['cumsum_amount'])*100
total_performance = total_performance[['Date','Day','Day_num','Quarter','Month','Year','cumsum_value','performance']]

#Accounts
account_hist = transactions.copy()
start_date = account_hist['Date'].min()

# Create dataframe with same structure as transaction to include the starting balances
data_acc = pd.DataFrame().reindex(columns=transactions.columns)
data_acc = data_acc.astype({'Date': 'datetime64[ns]', 'Amount': 'object', 'Account': 'object', 'Memo': 'object'})

# fill empty dataframe with starting account information on the first recorded day
for index, row in accounts.iterrows():
    data_acc.loc[index, 'Date'] = start_date
    data_acc.loc[index, 'Memo'] = 'starting balance'
    data_acc.loc[index, 'Account'] = row['Name']
    data_acc.loc[index, 'Amount'] = row['Start balance']

account_hist = (pd
                .concat([data_acc, account_hist], ignore_index=True)
                .groupby(['Date','Account'])["Amount"]
                .sum().reset_index()
                .sort_values(['Date'], ascending=[True])
)

#turn amount into float so it can be summed, then calculate running total by account
account_hist['Amount'] = pd.to_numeric(account_hist['Amount'])
account_hist['RT'] = account_hist.groupby(['Account'])['Amount'].cumsum()

loop_acc_start = True
for acc in accounts['Name']:
    temp_df = account_hist.loc[account_hist['Account']==acc,:]
    # merge with date table and fill down days with no transactions
    temp_df = pd.merge(date_table, temp_df, left_on="Date", right_on="Date", how="left").sort_values(by='Date', ascending=True)
    temp_df[['Account','RT']] = temp_df[['Account','RT']].ffill(axis = 0)
    
    if loop_acc_start :
        account_prog = temp_df.copy()
    else: 
        account_prog = pd.concat([account_prog, temp_df], ignore_index=True)
    
    loop_acc_start = False

#adding the stocks to account_prog
stocks_prog = pd.DataFrame().reindex(columns=account_prog.columns)
stocks_prog = stocks_prog.astype({'Date': 'datetime64[ns]', 'Day': 'object', 'Account': 'object', 'RT': 'float64'})

stocks_prog[['Account','RT']] = datetable_portfolio[['Ticker','cumsum_value']]
stocks_prog.iloc[:,0:7] = datetable_portfolio.iloc[:,0:7]

account_prog = pd.concat([account_prog, stocks_prog], ignore_index=True)
account_prog.drop(account_prog[account_prog.RT == 0].index, inplace=True)
account_prog['RT'] = account_prog['RT'].map(lambda x: float2dec(x))

#------------------------------------------------------------------------------
# App beginning
ext_css = "https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.5/font/bootstrap-icons.css"
load_figure_template(["bootstrap"])
app = dash.Dash(__name__, use_pages=True, external_stylesheets=[dbc.themes.FLATLY, dbc.icons.FONT_AWESOME, ext_css])

CONTENT_STYLE = {
    "margin-left": "18rem",
    "margin-right": "2rem",
    "padding": "2rem 1rem",
    "height" : "100vh"
}

header = html.Div([
    html.H4(
    "Expense Tracker v1", className="text-black text-center p-2 my-0"
    ),
],)

navlink_style = {
    'textAlign': 'center'
}

slider = html.Div([
        html.Div('Year(s)'),
        #html.Br(),
        dcc.RangeSlider(
            min=year_list[0],
            max=year_list[-1],
            value=[year_list[-1]],
            marks={i: str(i) for j, i in enumerate(year_list)},
            step=1,
            id="years_slider",
            tooltip={"placement": "bottom", "always_visible": False},
            className="p-2",
    )],
    className="my-3",
    style=navlink_style
)

sidebar = dbc.Col(
    [   
        html.Div([
            header,
            html.Hr(),
            slider,
            html.Hr(),
        ]),
        dbc.Nav(
            [
                dbc.NavLink([html.Div(className="fa-solid fa-bag-shopping"), html.Br(), html.Div("General")], href="/", active="exact", className='px-0', style=navlink_style),
                dbc.NavLink([html.Div(className="fa-solid fa-car"),html.Br(),"Car"], href="/car", active="exact", className='px-0',  style=navlink_style),
                dbc.NavLink([html.Div(className="fa-solid fa-arrow-trend-up"),html.Br(),"Investments"], href="/investments", active="exact", className='px-0',  style=navlink_style),
                dbc.NavLink([html.Div(className="fa-solid fa-building-columns"),html.Br(),"Accounts"], href="/accounts", active="exact", className='px-0',  style=navlink_style),
            ],
            vertical=True,
            pills=True,
            style={'fontSize' : 'small'}
        ),
    ],
    id="sidebar",
    style=navlink_style
)

app.layout = dbc.Container([
    dbc.Row([ 
        dbc.Col(sidebar, width=12, lg=1), 
        dbc.Col(dash.page_container, width=12, lg=11)
        ]),
    dcc.Store(id='df-transactions'),
    dcc.Store(id='df-trapay'),
    dcc.Store(id='df-trapayee'),
    dcc.Store(id='df-portfolio'),
    dcc.Store(id='df-performance'),
    dcc.Store(id='df-accounts')
    ],
    fluid=True,
    className="dbc dbc-ag-grid px-4 py-0",
)

@callback(
    Output('df-transactions', 'data'),
    Output('df-trapay', 'data'),
    Output('df-trapayee', 'data'),
    Output('df-portfolio', 'data'),
    Output('df-performance', 'data'),
    Output('df-accounts', 'data'),
    Input('years_slider', 'value'))
def selectYears(selected_years):
    filterTrans = transactions[
        (transactions['Year'] >= sorted(selected_years)[0]) & 
        (transactions['Year'] <= sorted(selected_years)[-1])
        ]

    #merge transaction with payees
    tra_pay = pd.merge(filterTrans, payees, left_on="Payee", right_on="id", how="left")
    tra_pay['Amount'] = (tra_pay['Amount'].map(float2dec) * float2dec(1)).map(float2dec)

    #create list of expense by payee
    tra_payee = tra_pay.groupby(['name', 'Year'])["Amount"].sum().reset_index().sort_values(['Year','Amount'], ascending=[False,True])

    filterPortfolio = datetable_portfolio[
        (datetable_portfolio['Year'] >= sorted(selected_years)[0]) & 
        (datetable_portfolio['Year'] <= sorted(selected_years)[-1])
        ]
    
    filterPerformance = total_performance[
        (datetable_portfolio['Year'] >= sorted(selected_years)[0]) & 
        (datetable_portfolio['Year'] <= sorted(selected_years)[-1])
        ]

    filterAccounts = account_prog[
        (account_prog['Year'] >= sorted(selected_years)[0]) & 
        (account_prog['Year'] <= sorted(selected_years)[-1])
        ]

    return filterTrans.to_json(), tra_pay.to_json(), tra_payee.to_json(), filterPortfolio.to_json(), filterPerformance.to_json(), filterAccounts.to_json()

if __name__ == "__main__":
    app.run_server(port=8888, debug=False)
