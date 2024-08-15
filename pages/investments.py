import pandas as pd
import numpy as np
from decimal import *
import dash
from dash import dcc, callback, Input, Output, Patch
import dash_ag_grid as dag
import dash_bootstrap_components as dbc
from dash_bootstrap_templates import load_figure_template
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from io import StringIO

load_figure_template(["bootstrap"])
dash.register_page(__name__, external_stylesheets=[dbc.themes.FLATLY, dbc.icons.FONT_AWESOME], path='/investments')

inv_dropdown = dcc.Dropdown(
    id='inv_dropdown',
    multi=True,
    persistence = True
)

investments_chart = dcc.Graph(
    id="investments_chart", 
    figure=go.Figure(), 
    style={'height': '100%'},
    className='py-0 my-0'
)

inv_table = dag.AgGrid(
        id="inv_table",
        columnSize="responsiveSizeToFit",
        columnSizeOptions={
            },
        dashGridOptions = {"rowHeight": 30},
        className="ag-theme-alpine"
        )

layout = dbc.Container(
    [   
        dbc.Row([
            dbc.Col([], width=0, lg=2,  style={"height" : "100%"}),
            dbc.Col([
               inv_table
            ], width=12, lg=8, style={"height" : "100%","display":"flex","justifyContent":"center","alignItems":"center"}),
            dbc.Col([], width=0, lg=2,  style={"height" : "100%"}),
        ], style={"display":"flex", "justifyContent" : "center", "alignItems" : "center" ,"height" : "30%"}),
        dbc.Row([
            dbc.Col([
                inv_dropdown
            ], width=12, style={"display":"flex", 
                                "justifyContent" : "center", 
                                "alignItems" : "end",
                                "marginTop" : "30px",
                                "marginBottom" : "10px"}),
            investments_chart
        ], style={"height" : "70%", "marginBottom" : "0", "marginTop" : "0"})
    ],
    id='invContainer',
    fluid=True,
    className="dbc dbc-ag-grid px-4 py-0",
    style={"border" : "3px solid white"}
)

#Dropdown
@callback(
    Output('inv_dropdown', 'options'),
    Output('inv_dropdown', 'value'),
    Input('df-portfolio', 'data'),
    )
def updateDropdown(data):
    datetable_portfolio = pd.read_json(StringIO(data))
    options = datetable_portfolio['Ticker'].dropna().unique()

    return options, options

#Chart
@callback(
    Output('investments_chart', 'figure'),
    Input('df-portfolio', 'data'),
    Input('inv_dropdown', 'value'),
    Input('df-performance', 'data'),
    )
def updatePortfolio(data, stock_list, perf):
    # decode from json
    datetable_portfolio = pd.read_json(StringIO(data))
    total_performance = pd.read_json(StringIO(perf))

    stockList = stock_list
    datetable_portfolio = datetable_portfolio.loc[datetable_portfolio['Ticker'].isin(stockList),:] 

    # total performance
    total_performance = datetable_portfolio.groupby(['Date','Day_num']).sum().reset_index().sort_values(['Date'], ascending=[True])
    total_performance['performance'] = \
        (total_performance['cumsum_value'] - abs(total_performance['cumsum_amount'])) / abs(total_performance['cumsum_amount'])*100
    total_performance = total_performance[['Date','Day','Day_num','Quarter','Month','Year','cumsum_value','performance']]

    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    for stock in stockList:
        cond = (datetable_portfolio['Ticker']==stock) & (datetable_portfolio['Day_num'].isin([1]))
        fig.add_trace(
                go.Bar(
                    x=datetable_portfolio.loc[cond ,'Date'],
                    y=datetable_portfolio.loc[cond, 'cumsum_amount']+ \
                    datetable_portfolio.loc[cond, 'cumsum_value'],
                    name=stock,
                    textposition='auto',
                    text=round(datetable_portfolio.loc[cond, 'cumsum_amount']+ \
                               datetable_portfolio.loc[cond, 'cumsum_value'],1),
                ),
                secondary_y=False
            )
    fig.update_layout(barmode="stack")
    cond2 = total_performance['Day_num'].isin([1])
    fig.add_trace(
            go.Scatter(
                x=total_performance.loc[cond2, 'Date'],
                y=total_performance.loc[cond2, 'performance'],
                name='Total performance',
                text=round(total_performance.loc[cond2, 'performance'],1).astype(str) +" %",
                mode="markers+lines+text",
                line=dict(
                    color="black"
                ),
                textposition='top left',
            ),
            secondary_y=True
        )
    
    fig.update_layout(
        margin=dict(l=0, r=0, t=0, b=20),
        showlegend=True
    )

    return fig

#table
@callback(
    Output('inv_table', 'rowData'),
    Output('inv_table', 'columnDefs'),
    Output('inv_table', 'dashGridOptions'),
    Output('inv_table', 'style'),
    Input('df-portfolio', 'data'),
    Input('df-performance', 'data')
)
def updateInvTable(data, perf):
    # decode from json
    datetable_portfolio = pd.read_json(StringIO(data))
    total_performance = pd.read_json(StringIO(perf))

    end_date = datetable_portfolio['Date'].max()
    portfolio = datetable_portfolio.loc[datetable_portfolio['Date']==end_date, :]
    portfolio = portfolio[['Ticker','cumsum_qty','cumsum_value','cumsum_amount']]
    portfolio['cumsum_value'] = round(pd.to_numeric(portfolio['cumsum_value']),2)

    portfolio = portfolio.rename(columns={'cumsum_amount': 'Total expense', 
                                          'cumsum_qty': 'total qty',
                                          'cumsum_value': 'Actual value',
                                          })
    portfolio['Var €'] = round(portfolio['Total expense'] + portfolio['Actual value'],2)
    portfolio['Var %'] = round(-portfolio['Var €']/portfolio['Total expense']*100,2).astype(str) + ' %'
    
    #set total row
    totals_row = portfolio.sum()
    totals_row.iloc[0] = "Totals"
    totals_row['Actual value'] = round(totals_row['Actual value'],2)
    totals_row.loc['total qty'] = np.NaN
    portfolio['Var €'] = (portfolio['Var €']).astype(str)
    totals_row['Var %'] = round(-totals_row['Var €']/totals_row['Total expense']*100,2).astype(str) + ' %'
    totals_row['Var €'] = (totals_row['Var €']).astype(str)

    rowData=portfolio.to_dict("records")
    columnlist = portfolio.columns

    columnDefs=[
                {
                "field": i, 
                "type": "rightAligned" if i != 'SubCat' else 'leftAligned',
                "sort": "asc" if i == 'Total' else False,
                'valueFormatter': {"function":"""d3.format(".2f")(params.value)"""} if i not in ['Ticker', 'Var %'] else False,
                'cellStyle': {
                    "function": "params.value < 0 || params.value.includes('-') ? {'color': 'red'} : {'color': 'green'}",
                    } if i in ['Var €', 'Var %'] else False
                } 
                for i in columnlist
            ]
    grid_option_patch = Patch()

    grid_option_patch["pinnedBottomRowData"] = [totals_row.to_dict()]
    #resize tab so it's always the right size
    grid_style = {'height': ((len(portfolio.index)+2)*30+4)}

    return rowData, columnDefs, grid_option_patch, grid_style