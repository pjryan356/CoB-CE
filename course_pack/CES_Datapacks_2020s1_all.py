import base64
import flask
import os
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
from collections import OrderedDict
from tabulate import tabulate

from IPython.core.interactiveshell import InteractiveShell

import sys
sys.path.append('c:\\Peter\\GitHub\\CoB\\')

import general.RMIT_colours as rc

from Course_enhancement_graphs import (
  line_graph_measure_surveys,
  line_graph_program_measure_surveys,
  generate_ces_pd_table,
  line_graph_gtsq_surveys,
  graphCourseProgramPie
)

from Course_enhancement_functions import (
  get_term_name,
  get_course_pop
)

from general.db_helper_functions import (
  connect_to_postgres_db,
  db_extract_query_to_dataframe
)

from general.postgres_queries import (
  qry_course_enhancement_list_2019s2
)

'''
This script is designed to produce the Course Enhancement Data Packs.
  On running it produces a weblink with two dropdown menus
  The School and Course need to be selected to display the data pack
  The Data Pack is then printed as a PDF (save with school and course_code)

The data is sourced from a local database which pre processes the data into the desired format
The data is pulled into 4 pandas dataframes
  df_ce (Original source - internal CoB documents)
    contains the course details of the courses undergoing course enhancement
    it is mainly used to produce the drop down menus and the queries for other dataframes
      level - academic level [HE, VE]
      school_code,
      course_code - ces course_code which includes clusters and vertical studios (-CL00),
      course_code_alt - regular course_code,
      school_name,
      course_name

  df_ce_ces (Original source - CES data summaries)
    contains the course level ces results for the past 5 years not all of the columns are used
      year, semester - of ces data
      level - academic level [HE, VE] used to determine which GTS questions were asked
      course_code -
      reliability - [G (good), S (sufficient), N (insufficient)] based on population and osi_response_count
      gts, gts_mean - gts percent agree [0-100] and mean gts [1-5]
      osi, osi_mean - osi percent agree [0-100] and mean osi [1-5]
      gts1, gts2, gts3, gts4, gts5, gts6 - percent agree for individual gts questions
      course_name
      course_coordinator
      population
      osi_response_count
      gts_response_count
  
  df_ce_comments (Original source - file supplied by Student Surveys Team)
    contains the de-identified and censored CES comments for the courses
    comments are from the selected year and semester (most recent available (or equivalent) survey results)
      program_code - program code of student, '' if 5 or less students from the program were enrolled in the course
      best - answer to What was the best aspect of this course?
      improve - answer to What part of this course needs the most improvement?
      course_code
  
  df_ce_prg_enrl (Original source - SAMS database)
    contains some enrolment details for the course (not all columns are used)
    enrolments are the selected year and semester (current, previous or previous equivalent)
      term_code
      course_code
      program_code - Non CoB program codes are combined as 'Non CoB'
      population - student enrolments in course and program
      program_name -
      school_code - Non CoB school codes are listed as 'Non CoB'
      school_name - Non CoB school names are listed as 'Non CoB'
      school - Non CoB school names are listed as 'Non CoB'
      school_colour - each CoB school has been assigned a colour from the RMIT palette for consistency
      college - college SAMS code
      college_name - Full college names
      college_name_short - changes BUS to CoB
      college_colour - each college has been assigned a colour from the RMIT palette for consistency

  df_ce_prg_ces (Original source - file supplied by Student Surveys Team)
      year, semester - of ces data
      level - academic level [HE, VE] used to determine which GTS questions were asked
      course_code -
      program_code -
      reliability - [G (good), S (sufficient), N (insufficient)] based on population and osi_response_count
      gts, gts_mean - gts percent agree [0-100] and mean gts [1-5]
      osi, osi_mean - osi percent agree [0-100] and mean osi [1-5]
      population
      osi_count
      gts_count
'''

'''------------------------------------- Set Inputs  --------------------------------'''
# Set parameter values
## Sometimes it asks for prompts twice I am not sure why
postgres_pw = input("Postgres Password: ")
start_year = 2017
year = 2020
semester = 1

# Setup app
app = dash.Dash(__name__)
app.css.config.serve_locally = True
app.scripts.config.serve_locally = True

''' ------------------- Add a css file to configure settings and layouts-------------'''
# The main css file used was copied from https://codepen.io/chriddyp/pen/bWLwgP.css
# When used 'directly' it had an undo/redo button located in bottom left corner of every page
# This was 'fixed' by appending the 'remove_undo.css' file
# In order to work the css files had to appended using the methodology outlined at
#   https://community.plot.ly/t/how-do-i-use-dash-to-add-local-css/4914/2
##  I do not fully understand how this works and sometimes it messes up

# app.css.append_css({"external_url": "https://codepen.io/chriddyp/pen/bWLwgP.css"}) # direct css usage

'''--------------------------------- Connect to Database  ----------------------------'''
# create postgres engine this is the connection to the postgres database

postgres_user = 'pjryan'
postgres_host = 'localhost'
postgres_dbname = 'postgres'

con_string = "host='{0}' " \
             "dbname='{1}' " \
             "user='{2}' " \
             "password='{3}' " \
             "".format(postgres_host, postgres_dbname, postgres_user, postgres_pw)

postgres_con, postgres_cur = connect_to_postgres_db(con_string)

'''------------------------Get Images---------------------'''
# header image
image_filename = 'C:\\Peter\\CoB\\logos\\L&T_Transparent_200.png'  # replace with your own image
logo = base64.b64encode(open(image_filename, 'rb').read())

# ces scale image (3 explanation)
image_filename = 'C:\\Peter\\CoB\\logos\\5_scale_mean.png'  # replace with your own image
ces_scale_image = base64.b64encode(open(image_filename, 'rb').read())

# ces scale image (3 explanation)
image_filename = 'C:\\Peter\\CoB\\logos\\mean_to_pa.png'  # replace with your own image
mean_pa_image = base64.b64encode(open(image_filename, 'rb').read())


'''------------------------------ Helper functions -----------------------------------'''

def list_to_text(obList):
  # converts a list of object into a string list for sql IN statement
  txt = "("
  for ob in obList:
    txt += "'{}',".format(ob)
  txt = txt[:-1] + ")"
  return txt

def get_gts_questions(level):
  # returns a list of the GTS questions for HE or VE
  if level == 'HE':
    gts_list = ['The teaching staff are extremely good at explaining things (SEi)',
                'The teaching staff normally give me helpful feedback on how I am going in this course (PE)',
                'The teaching staff motivate me to do my best work (SEi)',
                'The teaching staff work hard to make this course interesting (SEi)',
                'The teaching staff make a real effort to understand difficulties I might be having in this course (PE)',
                'The teaching staff put a lot of time into commenting on my work (PE)',
                '\*SEi: Student Engagement (impact);\u00A0\u00A0\*\*PE: Perceived Effort;']
  
  elif level == 'VE':
    gts_list = ['My instructors have a thorough knowledge of the course assessment (PC)',
                'My instructors provide opportunities to ask questions (SEp)',
                'My instructors treat me with respect (SEp)',
                'My instructors understand my learning needs (PC)',
                'My instructors communicate the course content effectively (SEi)',
                'My instructors make the course content as interesting as possible (SEi)',
                '\*PC: Perceived Capability;\u00A0\u00A0\*\*SEp: Student Engagement (practice);\u00A0\u00A0\*\*\*SEi: Student Engagement (impact);']
  else:
    gts_list = []
  
  return gts_list


def make_comments_rows(df1, empty_statement='No comments provided'):
  # creates a Dash table of comments from a panda data frame
  ## df should have 3 columns {program_code, best, improve}
  ## Empty df is empty: the empty_stement is placed in middle column
  ##    Postrges does not handle apostrophe and single quote marks well, they are often converted to a ?
  ##    hence all ? are converted to ', this is not perfect but creates less errors overall
  df1 = df1[['program_code', 'best', 'improve']]
  try:
    if len(df1) > 0:
      rows = [
        html.Tr(
          [html.Td(df1.iloc[i][col].replace("?", "'")) for col in df1.columns]
        ) for i in range(len(df1))
      ]
    else:
      rows = [html.Tr([html.Td(''), html.Td(empty_statement), html.Td('')])]
  except:
    raise
    
    rows = [html.Tr([html.Td(''), html.Td(empty_statement), html.Td('')])]
  return rows


'''----------------------------- create data extraction functions -------------------------------------'''


def qry_course_list(year, semester, tbl='vw0002_course_summaries', schema='ces'):
  # Returns a dataframe of the courses undergoing enhancement course in year, semester from db (cur)
  qry = " SELECT DISTINCT \n" \
        "   ces.level, ces.school_code, ces.course_code, \n" \
        "   ces.course_code_ces, \n" \
        "   ces.school, ces.course_name \n" \
        "	 FROM {0}.{1} ces \n" \
        " WHERE year = {2} AND semester = {3} \n" \
        " ORDER BY ces.school, ces.course_code \n" \
        "".format(schema, tbl,
                  year, semester)
  return qry

def get_course_list(year, semester, cur, tbl='vw0002_course_summaries', schema='ces'):
  # Returns a dataframe of the courses undergoing enhancement course in year, semester from db (cur)
  qry = qry_course_list(year, semester, tbl, schema)
  return db_extract_query_to_dataframe(qry, cur, print_messages=False)


def get_course_ces_data(course_list, start_year, end_year, cur, tbl='vw0002_course_summaries', schema='ces'):
  # Returns a dataframe with CES data for courses in course list
  qry = ' SELECT \n' \
        "   year, semester, level, \n" \
        "   course_code, \n" \
        "   course_code_ces, \n" \
        '   reliability, round(mgts, 2) AS gts, \n' \
        '   round(mosi, 2) AS osi, \n' \
        '   round(mgts1, 2) AS gts1, round(mgts2, 2) AS gts2, round(mgts3, 2) AS gts3, \n' \
        '   round(mgts4, 2) AS gts4, round(mgts5, 2) AS gts5, round(mgts6, 2) AS gts6, \n' \
        '   course_coordinator, population, osi_count, gts_count \n' \
        ' FROM {0}.{1} \n' \
        " WHERE course_code_ces IN {2} \n" \
        "	  AND year >= {3} \n" \
        "   AND year <= {4} \n" \
        " ORDER BY course_code_ces, year, semester; \n" \
        "".format(schema, tbl,
                  list_to_text(course_list),
                  start_year,
                  end_year)
  return db_extract_query_to_dataframe(qry, cur, print_messages=False)

def get_course_comments(course_list, year, semester, cur,
                        tbl='vw202_course_comments',
                        tbl2='vw0101_course_program',
                        schema='ces'):
  # Returns a dataframe with CES comments for courses in course list from
  qry = """
  SELECT * FROM (
  SELECT
  	CASE
      	WHEN pop.population <= 5 OR pop.population IS NULL THEN ''
      	ELSE comm.program_code END AS program_code,
  	COALESCE(best, '') AS best,
  	COALESCE(improve, '') AS improve,
  	pop.course_code, pop.course_code_ces
  FROM (
    	SELECT course_code, course_code_ces, program_code, best, improve
    	FROM {0}.{1}
    	WHERE year = {2} AND semester = {3} AND course_code_ces IN {4}
  	) comm
  LEFT OUTER JOIN (
      SELECT
      	pc.course_code,
      	pc.course_code_ces,
        pc.program_code,
        pc.population
      FROM {0}.{5} pc
      WHERE course_code_ces IN {4}
      	    AND year = {2}
      	    AND semester = {3}
  	) pop ON comm.program_code = pop.program_code AND comm.course_code_ces = pop.course_code_ces
  ) t1
  ORDER BY program_code
  """.format(schema, tbl,
             year, semester,
             list_to_text(course_list),
             tbl2)
  return db_extract_query_to_dataframe(qry, cur, print_messages=False)


def get_course_program_ces_data(course_list, start_year, end_year, cur, tbl='vw0101_course_program', schema='ces'):
  # Returns a dataframe with CES data for courses in course list
  qry = ' SELECT \n' \
        '   crse_prg.*, \n' \
        '   pd.program_name, \n' \
        "   CASE WHEN pd.college = 'BUS' THEN pd.school_code ELSE 'Not CoBL' END AS school_code, \n" \
        "   COALESCE(bsd.school_name_short, 'Not CoBL') AS school_name_short, \n" \
        "   CASE WHEN pd.college = 'BUS' THEN bsd.html ELSE '#FAC800' END AS school_colour, \n" \
        "   pd.college, \n" \
        "   col.college_name_short, \n" \
        "   col.html AS college_colour \n " \
        ' FROM ( \n' \
        '   SELECT \n' \
        "     year, semester, level,  \n" \
        "     course_code, course_code_ces, program_code, \n" \
        '     reliability, \n' \
        '     round(mgts, 2) AS gts, \n' \
        '     round(mosi, 2) AS osi, \n' \
        '     population::int, osi_count, gts_count \n' \
        '   FROM {0}.{1} \n' \
        "   WHERE course_code_ces IN {2} \n" \
        "     AND year >= {3} \n" \
        "     AND year <= {4} \n" \
        "   ) crse_prg \n" \
        " LEFT JOIN ( \n" \
        "   SELECT program_code, program_name, school_code, college \n" \
        "   FROM lookups.tbl_program_details \n" \
        "   ) pd ON (crse_prg.program_code = pd.program_code) \n" \
        " LEFT JOIN ( \n" \
        "   SELECT sd.school_code, sd.school_name_short, sc.html \n" \
        "   FROM (SELECT  school_code, school_name_short, colour FROM lookups.tbl_bus_school_details) sd \n" \
        "   LEFT JOIN (SELECT colour_name, html FROM lookups.tbl_rmit_colours) sc \n" \
        "     ON sc.colour_name = sd.colour \n" \
        "   ) bsd ON (pd.school_code=bsd.school_code)\n" \
        " LEFT JOIN ( \n" \
        "   SELECT cd.college_code, cd.college_name, cd.college_name_short, rc.html \n" \
        " 	FROM lookups.tbl_rmit_college_details cd, lookups.tbl_rmit_colours rc \n" \
        "   WHERE rc.colour_name = cd.colour \n" \
        "   ) col ON (pd.college = col.college_code) \n" \
        " ORDER BY course_code_ces, program_code, year, semester; \n" \
        "".format(schema, tbl,
                  list_to_text(course_list),
                  start_year,
                  end_year)
  return db_extract_query_to_dataframe(qry, cur, print_messages=False)


'''-------------------------------------------- Create Dataframes -------------------------------------'''
df_crse_list = get_course_list(year, semester,
                                    cur=postgres_cur)
df_schools = df_crse_list[['school_code', 'school']].drop_duplicates()

#print(df_crse_list)
#print(df_schools)

df_ces = get_course_ces_data(
  df_crse_list['course_code_ces'].tolist(),
  start_year,
  year,
  cur=postgres_cur)

#print(df_ces)

df_ces_comments = get_course_comments(
  df_crse_list['course_code_ces'].tolist(),
  year, semester,
  cur=postgres_cur)

#print(df_ces_comments)

df_crse_prg_ces = get_course_program_ces_data(
  df_crse_list['course_code_ces'].tolist(),
  start_year,
  year,
  cur=postgres_cur)
#print(df_crse_prg_ces)

'''----------------------------- create dash functions -------------------------------------'''
def create_school_options():
  # Create School options dropdown
  df_schools.sort_values(['school'])
  options = [{'label': '{1} ({0})'.format(r['school_code'],
                                          r['school']),
              'value': r['school_code']} for i, r in df_schools.iterrows()]
  options.insert(0, {'label': 'All', 'value': None})
  return options


def create_course_options(df1, school_code=None):
  # filters course list by given school code
  if school_code != None:
    f_df = df1.loc[df_crse_list['school_code'] == school_code]
  else:
    f_df = df1
  
  # Create Course options dropdown
  
  options = [{'label': '{0}: {1}'.format(r['course_code_ces'],
                                         r['course_name']),
              'value': r['course_code_ces']} for i, r in f_df.sort_values(['course_code_ces']).iterrows()]
  options.insert(0, {'label': 'All', 'value': None})
  return options


def get_course_data(df1, course_code_ces):
  # filters dataframe to given course_code
  try:
    return df1.loc[df1['course_code_ces'] == course_code_ces]
  except:
    try: df1.loc[df1['course_code'] == course_code_ces]
    except:
      pass
  return None

def make_program_page(course_code_ces, df1_prg_ces, df1_enrol, program_codes):
  # Function that creates the course Program Page for given course_code
  div = html.Div(
    [
      # Second row - Student distribution Heading
      html.Div(
        [
          html.P(
            [dcc.Markdown('**Student cohorts ({} Semester {})** '
                          '\u00A0 Population: {}'
                          ''.format(year, semester,
                                    get_course_pop(df1_enrol, course_code_ces,
                                                   year=year,
                                                   semester=semester)))
             ],
            style={'fontSize': 24,
                   'margin-left': 20, })
        ],
        className='twelve columns',
        style={'text-align': 'left'},
      ),
      # Third Row - Student distribution Pie Charts
      html.Div(
        children=[
          html.Div(  # Pie - Program
            [
              dcc.Graph(
                id='prg-pie-graph',
                figure=graphCourseProgramPie(df1_enrol, 'program'),
                style={'border': 'solid'},
              )
            ],
            className='four columns',
          ),
          html.Div(  # Pie - School
            [
              dcc.Graph(
                id='sch-pie-graph',
                figure=graphCourseProgramPie(df1_enrol, 'school'),
                style={'border': 'solid'},
              )
            ],
            className='four columns',
          ),
          html.Div(  # Pie - College
            [
              dcc.Graph(
                id='col-pie-graph',
                figure=graphCourseProgramPie(df1_enrol, 'college'),
                style={'border': 'solid'},
              )
            ],
            className='four columns',
          ),
        ],
        className='twelve columns',
        style={'margin-bottom': 10}
      ),
      # Fourth row - Program CES charts
      html.Div(
        className='row',
        style={'margin-bottom': 10,
               'margin-top': 0,
               'margin-left': 0,
               'margin-right': 0, },
        children=[
          html.Div(  # OSI - Program
            [
              dcc.Graph(
                id='prg-osi-graph',
                figure=line_graph_program_measure_surveys(
                  df1_prg_ces,
                  course_code_ces,
                  program_codes,
                  measure='osi',
                  start_year=start_year,
                  end_year=year, semester=None,
                  width=520, height=320,
                  mean=True),
                style={'border': 'solid'},
              )
            ],
            className='six columns',
          ),
          html.Div(  # GTS - Program
            [
              dcc.Graph(
                id='prg-gts-graph',
                figure=line_graph_program_measure_surveys(
                  df1_prg_ces,
                  course_code_ces,
                  program_codes,
                  measure='gts',
                  start_year=start_year,
                  end_year=year, semester=None,
                  width=520, height=320,
                  mean=True),
                style={'border': 'solid'},
              )
            ],
            className='six columns',
          ),
        ],
      ),
    ],
  )
  return div

def make_course_pack(course_code_ces):
  # Main function that creates the Data pack for given course_code
  ## Note the first page header is not included as it forms part of the selection box
  
  # filters data frames to selected course
  df1_crse = get_course_data(df_crse_list, course_code_ces)
  df1_ces = get_course_data(df_ces, course_code_ces)
  df1_comments = get_course_data(df_ces_comments, course_code_ces)
  df1_prg_ces = get_course_data(df_crse_prg_ces, course_code_ces)

  #print(tabulate(df1_crse, headers='keys'))
  #print(tabulate(df1_ces, headers='keys'))
  #print(tabulate(df1_comments, headers='keys'))
  #print(tabulate(df1_prg_ces, headers='keys'))
  
  # get top 5 programs in most recent semester
  df1_enrl = df1_prg_ces.loc[(df1_prg_ces['year'] == year) &
                             (df1_prg_ces['semester'] == semester)]
  program_codes = df1_enrl.sort_values('population', ascending=False).head(n=5)['program_code'].tolist()
  program_codes = list(OrderedDict.fromkeys(program_codes))
  
  try:
    level = df1_ces['level'].tolist()[-1]
  except:
    level = 'HE'
  
  gts_list = get_gts_questions(level)
  
  
  # create Data pack in correct layout
  child = [
    # First Page - CES quantitative data
    html.Div(
      [
        # First Row - OSI & GTS overtime graph and CES overtime table
        html.Div(
          [
            # OSI & GTS Graph
            html.Div(
              [
                dcc.Graph(
                  id='gts-graph',
                  figure=line_graph_measure_surveys(df1_ces, course_code_ces, ['gts', 'osi'], start_year, year,
                                                    semester=None,
                                                    width=540,
                                                    height=320,
                                                    mean=True),
                  style={'margin': 2},
                )
              ],
              className='six columns',
              style={'margin-left': 0,
                     'margin-right': 0}
            ),
            # CES Table
            html.Div(
              children=[
                dcc.Graph(
                  id='ces-table',
                  figure=generate_ces_pd_table(df1_ces, course_code_ces),
                  style={'margin': 0,
                         'margin-top': 5,
                         'margin-left': 30,
                         'margin-right': 10,
                         'margin-bottom': 0,
                         },
                )
              ],
              className='six columns',
              style={'margin': 0,
                     }
            ),
          ],
          className='twelve columns',
          style={'border': 'solid',
                 'margin-top': 5}
        ),
        # Second Row - Individual GTS questions graph and CES questions list
        html.Div(
          [
            # Individual GTS questions overtime graph
            html.Div(
              [
                dcc.Graph(
                  id='gtsi-graph',
                  figure=line_graph_gtsq_surveys(df1_ces,
                                                 course_code_ces,
                                                 start_year,
                                                 year, semester=None,
                                                 acad_career=level,
                                                 height=300,
                                                 mean=True),
                  style={'margin': 2,
                         },
                )
              ],
              className='six columns',
              style={'margin-left': 0,
                     'margin-right': 0},
            ),
            # CES question explanations
            html.Div(
              [
                html.P(['GTS Questions'],
                       style={'margin': 0,
                              'font-weight': 'bold'}),
                html.P(['Q1: {}'.format(gts_list[0])], style={'margin': '0'}),
                html.P(['Q2: {}'.format(gts_list[1])], style={'margin': '0'}),
                html.P(['Q3: {}'.format(gts_list[2])], style={'margin': '0'}),
                html.P(['Q4: {}'.format(gts_list[3])], style={'margin': '0'}),
                html.P(['Q5: {}'.format(gts_list[4])], style={'margin': '0'}),
                html.P(['Q6: {}'.format(gts_list[5])], style={'margin': '0'}),
                html.P([dcc.Markdown('{}'.format(gts_list[6]))],
                       style={'margin-top': '5'}),
                html.P([dcc.Markdown('**OSI:** {}'.format('Overall I am satisfied with the quality of this course'))],
                       style={'margin-top': '5'}),
              
              ],
              className='six columns',
              style={'margin-top': 20,
                     'margin-left': 30,
                     'margin-right': 0,
                     'margin-bottom': 0}
            ),
          ],
          className='twelve columns',
          style={'border': 'solid',
                 'margin-top': 5}
        )
      ],
      style={'width': '29.4cm',
             'height': '20.25cm',
             'top-margin': 0,
             'bottom-margin': 20,
             'right-margin': 50,
             'left-margin': 50}
    ),
    
    html.Div([html.P('')],
             className='twelve columns',
             style={'bottom-margin': 50},
             ),
    # Second Page - Program Distributions and CES data
    html.Div(
      [
        # First row - Page Header
        make_header_div(df1_crse),
        # Second row - Student distribution Heading
        make_program_page(course_code_ces, df1_prg_ces, df1_enrl, program_codes),
      ],
      style={'width': '29.4cm',
             'height': '19.9cm',
             'top-margin': 0,
             'bottom-margin': 0,
             'right-margin': 50,
             'left-margin': 50},
    ),
    html.Div([html.P('')],
             className='twelve columns',
             style={'bottom-margin': '50'},
             ),
  
    # Third Page - Additional Information
    html.Div(
      [
        # First row - Page Header
        make_header_div(df1_crse),
        # Second row - Heading
        html.Div(
          [
            html.P(
              children=[dcc.Markdown('**Additional Information**')],
              style={'fontSize': 24,
                     'margin-left': 20, })
          ],
          className='twelve columns',
          style={'text-align': 'left'},
        ),
        
        # Third row - Additional Information
        html.Div(
          className='row',
          style={'margin-bottom': 10,
                 'margin-top': 0,
                 'margin-left': 0,
                 'margin-right': 0, },
          children=[
            # GTS calculation explanation
            html.Div(
              className='six columns',
              style={'margin-bottom': 0,
                     'margin-top': 0,
                     'margin-left': 0,
                     'margin-right': 0, },
              children=
              [
                html.P(['How is the GTS calculated?'],
                       style={'textAlign': 'center',
                              'font-size': 16,
                              'color': rc.RMIT_Black,
                              'font-weight': 'bold',
                              'margin-bottom': 5,
                              'margin-top': 0,
                              'margin-left': 10,
                              'margin-right': 0},
                       ),
                html.P(['Students can complete the CES for each class they are enrolled in.'],
                       style={'textAlign': 'left',
                              'font-size': 16,
                              'color': rc.RMIT_Black,
                              'font-weight': 'normal',
                              'margin-bottom': 0,
                              'margin-left': 10},
                       ),
                html.P(['Students can answer the OSI and qualitative questions once per class. '
                        'Student can answer the six GTS questions once for every staff member in the course.'
                        ' Hence the total number of responses for the GTS is usually higher than for the OSI.'],
                       style={'textAlign': 'left',
                              'font-size': 16,
                              'color': rc.RMIT_Black,
                              'font-weight': 'normal',
                              'margin-bottom': 10,
                              'margin-left': 10},
                       ),
                html.P(['All CES questions are measured against a 5-point scale ranging from'
                        ' "Strongly Disagree" to "Strongly Agree".'],
                       style={'textAlign': 'left',
                              'font-size': 16,
                              'color': rc.RMIT_Black,
                              'font-weight': 'normal',
                              'margin-bottom': 0,
                              'margin-left': 10},
                       ),
                html.Img(
                  src='data:image/png;base64,{}'.format(ces_scale_image.decode()),
                  style={'height': '120px',
                         'width': '520px',
                         'align': 'middle',
                         'vertical-align': 'middle',
                         'margin-top': 10,
                         'margin-bottom': 10,
                         'margin-left': 10,
                         'margin-right': 0,
                         }
                ),
                html.P(['The mean GTS is the sum of responses from all 6 GTS questions for the course'
                        ' divided by the total number of responses.'],
                       style={'textAlign': 'left',
                              'font-size': 16,
                              'color': rc.RMIT_Black,
                              'font-weight': 'normal',
                              'margin-bottom': 5,
                              'margin-left': 10},
                       ),
                html.P(['The range of the mean GST (and OSI) is 1 to 5.'],
                       style={'textAlign': 'left',
                              'font-size': 16,
                              'color': rc.RMIT_Black,
                              'font-weight': 'normal',
                              'margin-bottom': 10,
                              'margin-left': 10},
                       ),
                html.P(
                  [dcc.Markdown(' The **reliability** (Rel) of the data in each survey is indicated by a letter:')],
                  style={'textAlign': 'left',
                         'font-size': 16,
                         'color': rc.RMIT_Black,
                         'font-weight': 'normal',
                         'margin-bottom': 0,
                         'margin-left': 10},
                  ),
                html.P([
                  '\u00A0\u00A0\u00A0\u00A0\u00A0\u00A0\u00A0G [Good]; S [Sufficient]; N [Insufficient]; or U [Unknown]'],
                  style={'textAlign': 'centered',
                         'font-size': 16,
                         'color': rc.RMIT_Black,
                         'font-weight': 'normal',
                         'margin-bottom': 10,
                         'margin-left': 10},
                ),
                html.P(
                  [dcc.Markdown(
                    'The **Qualitative Data** from the {} S{} CES is on the following pages.'
                    ''.format(year, semester))
                  ],
                  style={'textAlign': 'left',
                         'font-size': 16,
                         'color': rc.RMIT_Black,
                         'font-weight': 'normal',
                         'margin-bottom': 0,
                         'margin-left': 10
                         },
                ),
              ],
            ),
            # Chart explanations
            html.Div(
              className='six columns',
              style={'margin-bottom': 0,
                     'margin-top': 0,
                     'margin-left': 40,
                     'margin-right': 0, },
              children=
              [
                html.P(['Program Charts'],
                       style={'textAlign': 'center',
                              'font-size': 16,
                              'color': rc.RMIT_Black,
                              'font-weight': 'bold',
                              'margin-bottom': 5,
                              'margin-top': 0,
                              'margin-left': 0,
                              'margin-right': 0},
                       ),

                html.P(
                  [dcc.Markdown(
                    'The **pie charts** show what program, school and college the students in the course are from.'
                    ' Non CoBL programs are grouped together.'
                    ' The pie charts are based on {} S{} survey population.'
                    ''.format(year, semester))
                  ],
                  style={'textAlign': 'left',
                         'font-size': 16,
                         'color': rc.RMIT_Black,
                         'font-weight': 'normal',
                         'margin-bottom': 0,
                         'margin-left': 20
                         },
                ),
                html.P(
                  [dcc.Markdown('The **OSI and GTS Data by program** are graphed for the cohorts from the 5 largest programs.'
                   ' Any additional programs are included in Other (x)')
                  ],
                  style={'textAlign': 'left',
                         'font-size': 16,
                         'color': rc.RMIT_Black,
                         'font-weight': 'normal',
                         'margin-bottom': 5,
                         'margin-left': 20
                        },
                ),
                html.P(['Mean vs Percent Agree'],
                       style={'textAlign': 'center',
                              'font-size': 16,
                              'color': rc.RMIT_Black,
                              'font-weight': 'bold',
                              'margin-bottom': 5,
                              'margin-top': 0,
                              'margin-left': 0,
                              'margin-right': 0},
                       ),
  
                html.P(
                  [dcc.Markdown(
                    "The Chart below uses CES data from the past 3 years to provide a guide for"
                    " converting between 'Mean' and 'Percent Agree'.")
                  ],
                  style={'textAlign': 'left',
                         'font-size': 16,
                         'color': rc.RMIT_Black,
                         'font-weight': 'normal',
                         'margin-bottom': 0,
                         'margin-left': 20
                         },
                ),
                html.Img(
                  src='data:image/png;base64,{}'.format(mean_pa_image.decode()),
                  style={'height': '320px',
                         'width': '520px',
                         'align': 'middle',
                         'vertical-align': 'middle',
                         'margin-top': 5,
                         'margin-bottom': 0,
                         'margin-left': 10,
                         'margin-right': 0,
                         }
                ),
              ],
            ),
          ],
        ),
      ],
      style={'width': '29.4cm',
             'height': '19.9cm',
             'top-margin': 0,
             'bottom-margin': 0,
             'right-margin': 50,
             'left-margin': 50},
    ),
    html.Div([html.P('')],
             className='twelve columns',
             style={'bottom-margin': '50'},
             ),
    html.Div([html.P('')],
             className='twelve columns',
             style={'bottom-margin': '50'},
             ),
    html.Div([html.P('')],
             className='twelve columns',
             style={'bottom-margin': '50'},
             ),
    # Third page - Qualitative CES data
    ## Depending on the number of pages this will expanded to any number of pages
    html.Div(
      [
        # First row - Page Header
        make_header_div(df1_crse),
        # Second row - Heading
        html.Div(
          [
            html.P(
              [dcc.Markdown('**Qualitative data ({} Semester {})**'
                            ''.format(year, semester))],
              style={'fontSize': 24,
                     'margin-left': 20, })
          ],
          className='twelve columns',
          style={'text-align': 'left'},
        ),
        # Fourth row - Comments table
        html.Div(
          [
            # Table
            html.Div(
              [
                html.Table(
                  # Header
                  [
                    html.Tr(
                      [html.Th('Program', style={'width': 80, 'text-align': 'center'}),
                       html.Th('What was the best aspect of this course?', style={'width': 560}),
                       html.Th('What part of this course needs the most improvement?', style={'width': 560}),
                       ],
                      style={'border': 'solid',
                             }
                    )
                  ] +
                  
                  # Body
                  make_comments_rows(df1_comments),
                  style={'border': 'solid',
                         'alignment': 'centre',
                         },
                )
              ],
              className='twelve columns',
              style={'text-align': 'center'},
            ),
          ],
          className='twelve columns',
          style={'margin-bottom': 10}
        ),
      ],
      style={'width': '29.4cm',
             'height': '19.9cm',
             'top-margin': 0,
             'bottom-margin': 20,
             'right-margin': 25,
             'left-margin': 25, }
    ),
  ]
  return child


def make_header_div(df1):
  # creates course header with pre defined logo
  try:
    course_code = df1['course_code_ces'].tolist()[0]
    course_name = df1['course_name'].tolist()[0]
    school_name = df1['school'].tolist()[0]
    div = html.Div(
      [
        # Left - Headings
        html.Div(
          [
            # Heading
            html.Div(
              children='Course Pack',
              style={'textAlign': 'left',
                     'font-size': 18,
                     'color': rc.RMIT_Black,
                     'font-weight': 'bold',
                     'margin-left': 2
                     },
            ),
            # Sub Heading
            html.Div(
              [
                html.P(
                  children='{}: {}'.format(course_code, course_name),
                  style={'textAlign': 'left',
                         'font-size': 16,
                         'color': rc.RMIT_Black,
                         'font-weight': 'bold',
                         'margin-bottom': 0,
                         'margin-left': 2
                         },
                ),
                html.P(
                  children='{}'.format(school_name),
                  style={'textAlign': 'left',
                         'font-size': 16,
                         'color': rc.RMIT_Black,
                         'font-weight': 'bold',
                         'margin-left': 10,
                         'margin-top': 0},
                ),
              ],
            ),
          ],
          className='seven columns'
        ),
        # Right - Image (logo)
        html.Div(
          [
            html.Img(
              src='data:image/png;base64,{}'.format(logo.decode()),
              style={'height': '80px',
                     'align': 'middle',
                     'vertical-align': 'middle',
                     'margin-top': 2}
            ),
          ],
          className='five columns',
          style={'align': 'middle',
                 'vertical-align': 'middle'
                 }
        ),
      ],
      className='twelve columns',
      style={'border': 'solid'}
    )
  except:
    div = html.Div(
      [],
      className='twelve columns',
      style={'border': 'solid'}
    )
    

  return div


def make_header_div_selector():
  # Creates first header with course and school dropdown menus
  div = html.Div(
    [
      # Left - Dropdown menus
      html.Div(
        [
          # Heading
          html.Div(
            children='Course Pack',
            style={'textAlign': 'left',
                   'font-size': 18,
                   'color': rc.RMIT_Black,
                   'font-weight': 'bold',
                   'margin-left': 2
                   },
          ),
          # Dropdowns
          html.Div(
            [
              html.Div(
                [
                  dcc.Dropdown(
                    id='course-dropdown',
                    options=create_course_options(df_crse_list),
                    value=None,
                    placeholder="Select a Course",
                  ),
                ],
                className='ten columns',
                style={'font-size': 14,
                       'color': rc.RMIT_Black,
                       'font-weight': 'bold',
                       'border': 'None'}
              ),
              html.Div(
                [
                  dcc.Dropdown(
                    id='school-dropdown',
                    options=create_school_options(),
                    value=None,
                    placeholder="Select a School"
                  ),
                ],
                className='ten columns',
                style={'font-size': 14,
                       'color': rc.RMIT_Black,
                       'font-weight': 'bold'}
              ),
            ],
          ),
        ],
        className='seven columns'
      ),
      # Right - Image
      html.Div(
        [
          html.Img(
            src='data:image/png;base64,{}'.format(logo.decode()),
            style={'height': '80px',
                   'align': 'middle',
                   'vertical-align': 'middle',
                   'margin-top': 2}
          ),
        ],
        className='five columns',
        style={'align': 'middle',
               'vertical-align': 'middle'
               }
      ),
    ],
    className='twelve columns',
    style={'border': 'solid',
           'width': '29.4cm',
           'top-margin': 0,
           'bottom-margin': 0,
           'right-margin': 50,
           'left-margin': 50},
  )
  return div


# Create app layout
app.layout = html.Div(
  [
    html.Link(
      rel='stylesheet',
      href='/static/bWLwgP.css'
    ),
    html.Link(
      rel='stylesheet',
      href='/static/remove_undo.css'
    ),
    make_header_div_selector(),
    html.Div(
      id='course-pack'
    ),
  ]
)

'''----------------------- Main Graph Controlled ----------------------------------'''
'''---------------------- Options updates -----------------------------'''
''' Dropdowns'''

# Update course options based on school selection
@app.callback(Output('course-dropdown', 'options'),
              [Input('school-dropdown', 'value')])
def update_course_dropdown(school_code):
  return create_course_options(df_crse_list, school_code)


# Update the data pack based on course selection
@app.callback(
  Output('course-pack', 'children'),
  [Input('course-dropdown', 'value')],
)
def create_page(course_code_ces):
  return make_course_pack(course_code_ces)


# Upload css formats
css_directory = 'C:\\Peter\\GitHub\\CoB\\course_pack\\'
#stylesheets = ['bWLwgP.css', 'remove_undo.css']
#static_css_route = '/static/'
#print(css_directory)

@app.server.route('/static/<path:path>')
def static_file(path):
  static_folder = os.path.join(css_directory, 'static')
  return send_from_directory(static_folder, path)


if __name__ == '__main__':
  app.run_server(port=8050, host='127.0.0.2', debug=False)
