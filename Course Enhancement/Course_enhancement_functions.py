from tabulate import tabulate
import traceback
import pandas as pd

import sys
sys.path.append('c:\\Peter\\GitHub\\CoB\\')
import general.RMIT_colours as rc

colourList = [rc.RMIT_Red,
              rc.RMIT_Green,
              rc.RMIT_Blue,
              rc.RMIT_Orange,
              rc.RMIT_Purple,
              rc.RMIT_Yellow,
              rc.RMIT_DarkBlue,
              rc.RMIT_Pink,
              rc.RMIT_Black,
              rc.RMIT_Aqua,
              rc.RMIT_Lemon,
              rc.RMIT_Lavender,
              rc.RMIT_Azure,
              rc.RMIT_Teal,
              rc.RMIT_Arctic
              ]
'''--------------------------------- Common Functions ----------------------------------'''
def get_term_name(term_code, year=None, semester=None, level=None, short=False):
  '''
  :param term_code: RMIT term code
  :return: string 'Year Term_name'
  '''
  txt = ''
  try:    year = '20{}'.format(term_code[:2])
  except: year = ''

  try:
    term_txt = ''
    term = term_code[2:]
    if short == False:
      if term == '00':
          term_txt = 'Summer Semester'
      elif term in ['01', '03']:
          term_txt = 'Academic Year'
      elif term == '02':
          term_txt = 'Flexible Term'
      elif term in ['05', '10']:
          term_txt = 'Semester 1'
      elif term in ['45', '50']:
          term_txt = 'Semester 2'
      elif term == '20':
          term_txt = 'Offshore Semester 1'
      elif term == '30':
          term_txt = 'Offshore Semester 2'
      elif term == '60':
          term_txt = 'Offshore Semester 3'
      elif term == '70':
          term_txt = 'Offshore Semester 4'
      elif term == '78':
          term_txt = 'Spring Semester'
      elif term == '91':
          term_txt = 'Vietnam Semester 1'
      elif term == '92':
          term_txt = 'Vietnam Semester 2'
      elif term == '93':
          term_txt = 'Vietnam Semester 3'
  
    if short == True:
      if term in ['05', '10', '91', '20']:
        term_txt = 'S1'
      elif term in ['45', '50', '92', '60']:
        term_txt = 'S2'
      elif term in ['93']:
        term_txt = 'S3'
      else:
        term_txt = 'Irregular offering'
       
  except:
    term_txt = ''
  
  output = ''
  output += year
  
  if term_txt != '':
    output += ' {}'.format(term_txt)
  return output

def get_colour(measure, level = 'HE'):
  if measure == 'osi':
    return rc.RMIT_Green
  if measure == 'gts':
    return rc.RMIT_DarkBlue

  if level == 'HE':
    #  Perceived Effort
    if measure == 'gts2':
      return rc.RMIT_Red
    if measure == 'gts5':
      return rc.RMIT_Pink
    if measure == 'gts6':
      return rc.RMIT_Orange
    
    # Student Engagement (Impact)
    if measure == 'gts3':
      return rc.RMIT_Blue
    if measure == 'gts4':
      return rc.RMIT_Azure
    if measure == 'gts1':
      return rc.RMIT_Aqua

  if level == 'VE':
    
    # Student Engagement (Practise)
    if measure == 'gts2':
      return rc.RMIT_Purple
    if measure == 'gts3':
      return rc.RMIT_Lavender
    
    # Perceived Capability
    if measure == 'gts1':
      return rc.RMIT_Red
    if measure == 'gts4':
      return rc.RMIT_Pink

    # Student Engagement (Impact)
    if measure == 'gts5':
      return rc.RMIT_Blue
    if measure == 'gts6':
      return rc.RMIT_Azure
  
  return rc.RMIT_Black

def get_course_pop(df1, term_code, course_code):
  try:
    df1_filter = df1.loc[(df1['term_code'] == term_code) &
                         (df1['course_code'] == course_code)]
    
    pop = int(df1_filter['population'].agg('sum'))
    return (pop)
  except:
    return None




