

import plotly.graph_objs as go

import sys
sys.path.append('c:\\Peter\\GitHub\\CoB\\')

import general.RMIT_colours as rc

from general.db_helper_functions import (
  connect_to_postgres_db,
  db_extract_query_to_dataframe
)
from tabulate import tabulate

import dash
import dash_core_components as dcc
import dash_html_components as html

import base64

from general.db_helper_functions import (
  connect_to_postgres_db,
  db_extract_query_to_dataframe
)

from Course_Enhancement_comparison import (
  create_ce_comparison_chart
)

from School_performance_report import (
  get_school_data,
  create_school_RMIT_graph,
  create_CoB_graph
)
year = 2018
semester = 2

start_year = 2015
end_year = 2018

'''--------------------------------- Connect to Database  ----------------------------'''
# create postgres engine this is the connection to the postgres database
postgres_pw = input("Postgres Password: ")
postgres_user = 'pjryan'
postgres_host = 'localhost'
postgres_dbname = 'postgres'

con_string = "host='{0}' " \
             "dbname='{1}' " \
             "user='{2}' " \
             "password='{3}' " \
             "".format(postgres_host, postgres_dbname, postgres_user, postgres_pw)
con, postgres_cur = connect_to_postgres_db(con_string)


'''------------------------Get Images---------------------'''
# header image
image_filename = 'C:\\Peter\\CoB\\logos\\L&T_Transparent_200.png'  # replace with your own image
logo = base64.b64encode(open(image_filename, 'rb').read())


'''------------------------Get Data-----------------------'''
qry = ' SELECT \n' \
      '   year, semester, level, school_name_short, colour, colour_html, \n' \
      '   population, gts, osi\n' \
      ' FROM ces.vw998_school_from_course_summaries_for_graph \n' \
      " WHERE  \n" \
      "   year >= {} AND year <= {} \n" \
      "".format(start_year, end_year);

df_schools_data = db_extract_query_to_dataframe(qry, postgres_cur, print_messages=False)
# print(tabulate(df_schools_data, headers='keys'))

df_schools_data = get_school_data(start_year, postgres_cur)
# print(tabulate(df_schools_data, headers='keys'))

qry = ' SELECT \n' \
      '   year, semester, level, college, college_name, college_name_short, colour, colour_html, \n' \
      '   population, gts, osi, gts_mean, osi_mean \n' \
      ' FROM ces.vw156_college_for_graph \n' \
      " WHERE college_name_short = 'CoB' AND level='HE'\n";

df_cob = db_extract_query_to_dataframe(qry, postgres_cur, print_messages=False)




def make_header():
  x = [
    # Left - Headings
    make_red_heading_div(),
  ]
  return x


def make_red_heading_div():

  style = {'text-align': 'center',
           'font-size': 36,
           'color': rc.RMIT_White,
           'font-family': 'Sans-serif',
           'font-weight': 'bold',
           'margin-left': 10,
           'margin-right': 10,
           'margin-bottom': 10,
           'margin-top': 10,
           'backgroundColor': rc.RMIT_Red,
           'line-height': 'normal'}
  
  div = html.Div(
    children=[
      html.P(children='CoB Schools    CES Results {1}'.format(semester, year),
             style=style),
    ],
    className='twelve columns',
    style={'backgroundColor': rc.RMIT_Red,
           'margin-left': 0,
           'margin-right': 0,
           }
  )
  return div


def make_ces_measure_section(measure, df=df_schools_data, start_year=2015, end_year=2018):
  div = \
    html.Div(
      className='row',
      style={'margin-bottom': 0,
             'margin-left': 0,
             'margin-right': 0,
             'backgroundColor': rc.RMIT_White,
             },
      children=[
        # Graph Title #################################################
        html.Div(
          className='row',
          style={'margin-bottom': 0,
                 'margin-left': 4,
                 'margin-right': 4,
                 'backgroundColor': rc.RMIT_DarkBlue,
                 },
          children=[
            
            html.Div(
              className='row',
              children=['CoB School CES {} Results'.format(measure.upper())],
              style={'backgroundColor': rc.RMIT_DarkBlue,
                     'textAlign': 'center',
                     'font-size': 28,
                     'color': rc.RMIT_White,
                     'font-family': 'Sans-serif',
                     'font-weight': 'normal',
                     'line-height': '150%',
                     'align': 'center',
                     'margin-top': 2,
                     },
            ),
          ],
        ),
        # Table ################################################################
        html.Div(
          className='row',
          style={'margin-bottom': 0,
                 'margin-left': 0,
                 'margin-right': 0,
                 'margin-top': 0,
                 'backgroundColor': rc.RMIT_White,
                 },
    
          children=[
            dcc.Graph(
              id='{}-table'.format(measure),
              figure=generate_school_ces_pd_table(df, start_year, end_year, measure),
              style={'margin': 0,
                     'margin-top': 0,
                     'margin-left': 250,
                     'margin-right': 0,
                     'backgroundColor': rc.RMIT_White},
            ),
          ],
        ),
        # Semester Titles #############################################
        html.Div(
          className='row',
          style={'margin-bottom': 0,
                 'margin-left': 4,
                 'margin-right': 4,
                 'backgroundColor': rc.RMIT_White,
                 },
          children=[
            # Semester 1
            html.Div(
              className='six columns',
              style={'margin-left': 10,
                     'margin-right': 5,
                     'margin-top': 0,
                     'backgroundColor': rc.RMIT_White,
                     },
              children=[
                html.P(children='Semester 1',
                       style={'text-align': 'center',
                              'font-size': 16,
                              'font-family': 'Sans-serif',
                              'font-weight': 'Bold',
                              'color': rc.RMIT_White,
                              'line-height': '100%',
                              'margin-left': 5,
                              'margin-right': 5,
                              'margin-top': 2,
                              'margin-bottom': 2,
                              'backgroundColor': rc.RMIT_Blue,
                              },
                       ),
              ],
            ),
            # Semester 2
            html.Div(
              className='six columns',
              style={'margin-left': 10,
                     'margin-right': 5,
                     'margin-top': 0,
                     'backgroundColor': rc.RMIT_White,
                     },
              children=[
                html.P(children='Semester 2',
                       style={'text-align': 'center',
                              'font-size': 16,
                              'font-family': 'Sans-serif',
                              'font-weight': 'Bold',
                              'color': rc.RMIT_White,
                              'line-height': '100%',
                              'margin-left': 5,
                              'margin-right': 5,
                              'margin-top': 2,
                              'margin-bottom': 2,
                              'backgroundColor': rc.RMIT_Blue,
                              },
                       ),
              ],
            ),
          ],
        ),
        # Graphs #############################################################
        html.Div(
          className='row',
          style={'margin-bottom': 0,
                 'margin-left': 0,
                 'margin-right': 0,
                 'margin-top': 0,
                 'backgroundColor': rc.RMIT_White,
                 },
          
          children=[
            # OSI Sem 1 Graph
            html.Div(
              className='six columns',
              style={'margin-left': 0,
                     'margin-right': 10,
                     'margin-top': 0,
                     'backgroundColor': rc.RMIT_White,
                     },
              
              children=[
                dcc.Graph(
                  id='{}-graph1'.format(measure),
                  figure=create_school_RMIT_graph(
                    df1=df,
                    measure=measure,
                    start_year=start_year, end_year=end_year,
                    semester=1,
                    height=340,
                    width=530,
                    background='#FFFFFF',
                    df_cob=df_cob)
                )
              ],
            ),
            # OSI Sem 2 Graph
            html.Div(
              className='six columns',
              style={'margin-left': 20,
                     'margin-right': 0,
                     'margin-top': 0,
                     'backgroundColor': rc.RMIT_White,
                     },
              
              children=[
                dcc.Graph(
                  id='{}-graph2'.format(measure),
                  figure=create_school_RMIT_graph(
                    df1=df,
                    measure=measure,
                    start_year=start_year, end_year=end_year,
                    semester=2,
                    height=340,
                    width=530,
                    background='#FFFFFF',
                    df_cob=df_cob)
                )
              ],
            ),
          ],
        ),
      ],
    )
  return div


def generate_school_ces_pd_table(df1, start_year, end_year, measure):
  f_df = df1.loc[(df1['year'] >= start_year)
                 & (df1['year'] <= end_year)
                 & (df1['school_name_short'] != 'CPO')]
  f_df = f_df.round({'{}'.format(measure): 1})
  
  f_df_cob = df_cob.loc[(df_cob['year'] >= start_year)
                        & (df_cob['year'] <= end_year)]
  f_df_cob = f_df_cob.round({'{}'.format(measure): 1})

  
  f_df_acct = f_df.loc[(f_df['school_name_short'] == 'ACCT')]
  f_df_bitl = f_df.loc[(f_df['school_name_short'] == 'BITL')]
  f_df_efm = f_df.loc[(f_df['school_name_short'] == 'EFM')]
  f_df_gsbl = f_df.loc[(f_df['school_name_short'] == 'GSBL')]
  f_df_mgt = f_df.loc[(f_df['school_name_short'] == 'MGT')]
  f_df_vbehe = f_df.loc[(f_df['school_name_short'] == 'VBE') & (f_df['level'] == 'HE')]
  f_df_vbeve = f_df.loc[(f_df['school_name_short'] == 'VBE') & (f_df['level'] == 'VE')]

  
  
  h = [' <br>Year<br><br>', ' <br>S<br><br>',
       ' <br>ACCT<br> ___ <br>', ' <br>BITL<br> ___ <br>',
       ' <br>EFM<br> ___ <br>', ' <br>GSBL<br> ___ <br>',
       ' <br>MGT<br> ___ <br>',
       'VBE<br>(HE)<br> ___ <br>', 'VBE<br>(VE)<br> .... <br>',
       'CoB<br>(HE)<br> ___ <br>'
       ]
  trace = go.Table(
    type='table',
    columnorder=(1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11),
    columnwidth=[20, 10, 20, 20, 20, 20, 20, 20, 20, 20, 20],
    header=dict(line=dict(color=[rc.RMIT_White, rc.RMIT_White,
                                 rc.RMIT_White, rc.RMIT_White,
                                 rc.RMIT_White, rc.RMIT_White,
                                 rc.RMIT_White,
                                 rc.RMIT_White, rc.RMIT_White,
                                 rc.RMIT_Black
                                 ]),
                values=h,
                align='center',
                font=dict(size=18,
                          color=[rc.RMIT_White, rc.RMIT_White,
                                 f_df_acct.iloc[0]['colour_html'], f_df_bitl.iloc[0]['colour_html'],
                                 f_df_efm.iloc[0]['colour_html'], f_df_gsbl.iloc[0]['colour_html'],
                                 f_df_mgt.iloc[0]['colour_html'],
                                 f_df_vbehe.iloc[0]['colour_html'], f_df_vbeve.iloc[0]['colour_html'],
                                 rc.RMIT_Black,
                                 ]
                          ),
                height=40,
                format=dict(border='solid'),
                fill=dict(color=[rc.RMIT_DarkBlue, rc.RMIT_DarkBlue,
                                 rc.RMIT_DarkBlue, rc.RMIT_DarkBlue,
                                 rc.RMIT_DarkBlue, rc.RMIT_DarkBlue,
                                 rc.RMIT_DarkBlue,
                                 rc.RMIT_DarkBlue, rc.RMIT_DarkBlue,
                                 rc.RMIT_White
                                 ])
                ),
    cells=dict(line=dict(color=[rc.RMIT_White, rc.RMIT_White,
                                rc.RMIT_White, rc.RMIT_White,
                                rc.RMIT_White, rc.RMIT_White,
                                rc.RMIT_White,
                                rc.RMIT_White, rc.RMIT_White,
                                rc.RMIT_White
                                ]),
               values=[f_df_acct.year, f_df_acct.semester,
                       f_df_acct['{}'.format(measure)], f_df_bitl['{}'.format(measure)],
                       f_df_efm['{}'.format(measure)], f_df_gsbl['{}'.format(measure)],
                       f_df_mgt['{}'.format(measure)],
                       f_df_vbehe['{}'.format(measure)], f_df_vbeve['{}'.format(measure)],
                       f_df_cob['{}'.format(measure)]
                       ],
               font=dict(size=12,
                         color=[rc.RMIT_White, rc.RMIT_White,
                                rc.RMIT_Black, rc.RMIT_Black,
                                rc.RMIT_Black, rc.RMIT_Black,
                                rc.RMIT_Black,
                                rc.RMIT_Black, rc.RMIT_Black,
                                rc.RMIT_White, rc.RMIT_White]),
               height=28,
               format=dict(border='solid'),
               fill=dict(
                 color=[rc.RMIT_DarkBlue, rc.RMIT_DarkBlue,
                        rc.RMIT_Arctic, rc.RMIT_Arctic,
                        rc.RMIT_Azure, rc.RMIT_Azure,
                        rc.RMIT_Arctic,
                        rc.RMIT_Azure, rc.RMIT_Azure,
                        rc.RMIT_Black,
                        ]),
               ),
  )
  
  layout = go.Layout(width=600,
                     height=355,
                     margin=dict(b=10, l=10, r=10, t=10))
  data = [trace]
  fig = dict(data=data, layout=layout)
  return fig


# Setup app
app = dash.Dash()
app.scripts.config.serve_locally = True
app.css.append_css({"external_url": "https://codepen.io/chriddyp/pen/bWLwgP.css"})

# Create app layout
app.layout = html.Div(
  [
    # Measures
    make_ces_measure_section('osi', df_schools_data, start_year, end_year),
    make_ces_measure_section('gts', df_schools_data,  start_year, end_year),
  ],
  style={'width': '29.4cm',
         'height': '20.25',
         'top-margin': '50',
         'bottom-margin': '50',
         'right-margin': '25',
         'left-margin': '25',
         'border': 'None',
         },
)

# In[]:
# More Helper functions
if __name__ == '__main__':
  app.run_server(port=8050, host='127.0.0.3', debug=True)

