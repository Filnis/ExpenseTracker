import pandas as pd
from decimal import *
import calendar
import dash
from dash import html, dcc, callback, Input, Output, html, dash_table, Patch
import dash_ag_grid as dag
import dash_bootstrap_components as dbc
from dash_bootstrap_templates import load_figure_template
import plotly.express as px
from io import StringIO
from support_functions import float2dec, create_card

load_figure_template(["bootstrap"])
dash.register_page(__name__, external_stylesheets=[dbc.themes.FLATLY, dbc.icons.FONT_AWESOME], path='/')

toggle = html.Div(
    [
        dbc.Checklist(
            id="switch-investments",
            options=[{"label": "Investments", "value": True}],
            value=[True],
            switch=True,
        ),
        dbc.Checklist(
            id="switch-months",
            options=[{"label": "Show months", "value": False}],
            value=[False],
            switch=True,
        ),
    ],
    className="mt-4",
)

cards = html.Div([
], id='side_cards')

controls = dbc.Row(toggle)

tab1 = dbc.Tab([dcc.Graph(
        id="monthly_balance",
        figure=px.bar(),
        style={'height': '70vh'}
        )], 
    label="Monthly Balance")
tab2 = dbc.Tab([dcc.Graph(
        id="top_15_payees", 
        figure=px.bar(), 
        style={'height': '70vh'}
        )], 
    label="Top 15 Payees")
tab3 = dbc.Tab([dag.AgGrid(
        style={"height": 800},
        id="category_grid",
        columnSize="responsiveSizeToFit",
        columnSizeOptions={
                'defaultMinWidth': 90,
                'defaultMaxWidth': 110,
                'columnLimits': [{'key': 'Cat', 'minWidth': 165}, {'key': 'Total', 'minWidth': 100}]
            },
        dashGridOptions = {"rowHeight": 30}
        )
    ],
    label="Categories by Month", 
    )

tab4 = dbc.Tab(
    [
        dag.AgGrid(
        style={"height": 550},
        id="transactions_grid",
        columnSize="responsiveSizeToFit",
        dashGridOptions = {"rowHeight": 30},
        columnSizeOptions={
                'columnLimits': [{'key': 'Month', 'maxWidth': 110}, {'key': 'Year', 'maxWidth': 100}]
            },
        persistence = True
        )
    ],
    label='Transactions'
)

tabs = dbc.Card(dbc.Tabs([tab3, tab4, tab1, tab2]))

width_control = 2
width_cards = 12 - width_control

layout = dbc.Container(
    [
        dbc.Row([
            dbc.Row([
                dbc.Col([
                    toggle
                ], width=12, lg=width_control),
                dbc.Col([
                    cards,
                ],width=12, lg=width_cards),
                html.Br()
            ]),
            dbc.Row([
                dbc.Col([tabs], width=12, lg=12),
            ])
        ]),
    ],
    id='expContainer',
    fluid=True,
    className="dbc dbc-ag-grid px-4 py-0",
)

def placeCards(cardList, w):
    children = []
    for card in cardList:
        children.insert(
            0,
            dbc.Col([
                card
            ],width=12/len(cardList))
        )
    return dbc.Row(children)
    
#Categories by month + Cards
@callback(
    Output('category_grid', 'rowData'),
    Output('category_grid', 'columnDefs'),
    Output('category_grid', 'dashGridOptions'),
    Output('category_grid', 'style'),
    Output('side_cards','children'),
    Input('switch-investments', 'value'),
    Input('switch-months', 'value'),
    Input('df-transactions', 'data'))
def updateCategoryTable(invest, show_months, data):
    # decode from json
    transactions = pd.read_json(StringIO(data))

    transactions['Amount'] = (transactions['Amount'].map(float2dec) * float2dec(1)).map(float2dec)
    tra_cat = transactions[['Year','Month','Cat','SubCat','Amount']]
    tra_cat = tra_cat[(tra_cat['Cat'] != '')]
    
    if not invest:
        tra_cat = tra_cat[tra_cat['Cat'] != "Investments"]
    else:
        tra_cat = tra_cat[:]

    tra_cat = pd.pivot_table(tra_cat, values='Amount', columns=['Year', 'Month'], index='Cat', aggfunc="sum")
    tra_cat.columns = [' '.join([calendar.month_abbr[col[1]], str(col[0])[-2:]]) for col in tra_cat.columns.values]
    tra_cat = tra_cat.reset_index(drop=False)
    n_months = len(tra_cat.columns)-1
    tra_cat['Total'] = tra_cat.iloc[:,-n_months:].sum(axis=1)
    
    # Balance: sum of positive + negative values
    totals = tra_cat.sum()
    totals.iloc[0] = 'Balance'

    # Expenses: sum of the negative values only
    tra_cat_num_neg = tra_cat.copy()
    tra_cat_num_neg.iloc[:, 1:] = tra_cat_num_neg.iloc[:, 1:].clip(upper=0)
    totals_negative = tra_cat_num_neg.sum()
    totals_negative.iloc[0] = 'Expenses'

    # Earnings: sum of the positive values only
    tra_cat_num_pos = tra_cat.copy()
    tra_cat_num_pos.iloc[:, 1:] = tra_cat_num_pos.iloc[:, 1:].clip(lower=0)
    totals_positive = tra_cat_num_pos.sum()
    totals_positive.iloc[0] = 'Earnings'

    # Percentage of each category compared to total expense
    tra_cat['Exp %'] = 0.0
    tra_cat['Exp %'] = pd.to_numeric(abs(tra_cat['Total'])) / pd.to_numeric(abs(totals_negative.iloc[-1]))*100
    tra_cat['Exp %'] = (tra_cat['Exp %'].map(float2dec) * float2dec(1)).map(float2dec).astype(str) + '%'

    # Percentage of each category compared to total earning
    tra_cat['Earn %'] = 0.0
    tra_cat['Earn %'] = pd.to_numeric(abs(tra_cat['Total'])) / pd.to_numeric(totals_positive.iloc[-1])*100
    tra_cat['Earn %'] = (tra_cat['Earn %'].map(float2dec) * float2dec(1)).map(float2dec).astype(str) + '%'

    totals_negative['Earn %'] = abs(totals_negative['Total'])/totals_positive['Total']*100
    totals_negative['Earn %'] = str(float2dec(totals_negative['Earn %'])) + '%'

    rowData=tra_cat.to_dict("records")

    if show_months:
        columnlist = tra_cat.columns 
    else: 
        columnlist = ['Cat','Total','Exp %','Earn %']
    
    columnDefs=[
                {
                "field": i, 
                "type": "rightAligned" if i != 'Cat' else 'leftAligned',
                "pinned": "left" if i == 'Cat' else 'left' if i in ['Total','Exp %','Earn %'] else False,
                "sort": "asc" if i == 'Total' else False,
                'valueFormatter': {"function":"""d3.format(".2f")(params.value)"""} if i not in ['Cat','Exp %','Earn %'] else False,
                'cellStyle': {
                    "function": "params.value < 0 ? {'color': 'red'} : {'color': 'green'}",
                    } if i not in ['Cat','Exp %','Earn %'] else False
                } 
                for i in columnlist
            ]
    grid_option_patch = Patch()

    #resize tab so it's always the right size
    grid_style = {'height': (len(tra_cat.index)+3)*30+70}
    
    grid_option_patch["pinnedBottomRowData"] = [totals_negative.to_dict(), totals_positive.to_dict(), totals.to_dict()]

    #Calculations for side cards
    if min(transactions['Year']) != max(transactions['Year']):
        selected_years = [min(transactions['Year']), max(transactions['Year'])]
    else:
        selected_years = min(transactions['Year'])
    #current year
    current_expense = totals_negative['Total']
    current_balance = totals['Total']
    current_earning = totals_positive['Total']

    card_expenses = create_card('Expenses ' + str(selected_years),'€ ' + str(current_expense))
    card_expenses.color = 'warning'
    card_expenses.inverse = True

    card_balance = create_card('Balance ' + str(selected_years),'€ ' + str(current_balance))
    card_balance.color = 'success' if current_balance >= 0 else 'danger'
    card_balance.inverse=True

    card_earning = create_card('Earnings  ' + str(selected_years),'€ ' + str(current_earning ))
    card_earning.color = 'success'
    card_earning.inverse=1

    return rowData, columnDefs, grid_option_patch, grid_style, placeCards([card_balance, card_earning, card_expenses],width_cards)

#Monthly balance
@callback(
    Output('monthly_balance', 'figure'), 
    Input('switch-investments', 'value'),
    Input('df-trapay', 'data'))
def updateMonthlyBalance(invest, data):
    # decode from json
    tra_pay = pd.read_json(StringIO(data))

    if not invest:
        tra_pay_temp = tra_pay[tra_pay['Cat'] != "Investments"]
    else:
        tra_pay_temp = tra_pay[:]

    tra_month = tra_pay_temp.groupby(['Year', 'Month'])["Amount"].sum().reset_index().sort_values(['Year','Month'], ascending=[False,False])

    month_balance_x = tra_month['Year'].astype(str) + " - " + tra_month['Month'].apply(lambda x: calendar.month_abbr[x])

    fig1 = px.bar(x=month_balance_x.iloc[::-1], 
                  y=tra_month['Amount'].iloc[::-1], 
                  text=round(tra_month['Amount'].iloc[::-1], 1))
    fig1.update_traces(textposition='outside',
                       marker_color=tra_month['Amount'].iloc[::-1].apply(lambda x: "#198754" if x > 0 else "#dc3545"))
    fig1.update_layout(transition_duration=0,
                        xaxis_title="Date",
                        yaxis_title="€")
    return fig1

# Top payees
@callback(
    Output('top_15_payees', 'figure'), 
    Input('df-trapayee', 'data'))

def updateTopPayees(data):
    # decode from json
    tra_payee = pd.read_json(StringIO(data))
    top_15_payees = tra_payee[(tra_payee['Amount']!=0) & (tra_payee['name'] != '---')]
    top_15_payees_select = top_15_payees.groupby(['name'])["Amount"].sum().reset_index().sort_values(['Amount'], ascending=[True]).head(15)
    top_15_payees = top_15_payees[top_15_payees['name'].isin(top_15_payees_select['name'])]
    top_15_payees = top_15_payees.groupby(['name','Year'])["Amount"].sum().reset_index(name ='Amount')
    fig2 = px.bar(top_15_payees, 
                  y=top_15_payees['name'], 
                  x=abs(top_15_payees['Amount']), 
                  color=top_15_payees['Year'].astype(str), 
                  text=round(top_15_payees['Amount'], 0), 
                  orientation='h')
    fig2.update_traces(textposition='auto')
    fig2.update_layout(barmode='stack', yaxis={'categoryorder':'total ascending'})    
    return fig2

@callback(
    Output('transactions_grid', 'rowData'),
    Output('transactions_grid', 'columnDefs'),
    Input('switch-investments', 'value'),
    Input('df-trapay', 'data'))
def updateTopPayees(invest, data):
    # decode from json
    tra_pay = pd.read_json(StringIO(data))
    tra_pay['Amount'] = (tra_pay['Amount'].map(float2dec) * float2dec(1)).map(float2dec)
    tra_pay['Date'] = tra_pay['Date'].dt.date
    
    if not invest:
        tra_pay = tra_pay[tra_pay['Cat'] != "Investments"]
    else:
        tra_pay = tra_pay[:]

    rowData=tra_pay.to_dict("records")
    columnlist = ['Date','Year','Month','Memo','Amount','Category','Account','name']

    columnDefs=[
                {
                "field": i, 
                "sort": "desc" if i == 'Date' else False,
                'cellStyle': {
                    "function": "params.value < 0 ? {'color': 'red'} : {'color': 'green'}",
                    } if i == 'Amount' else False,
                'filter': 'agDateColumnFilter' if i == 'Date' else True,
                "filterParams": {
                    "buttons": ["reset"],
                    "closeOnApply": True,
                },
                'floatingFilter': True
                } 
                for i in columnlist
            ]
    return rowData, columnDefs