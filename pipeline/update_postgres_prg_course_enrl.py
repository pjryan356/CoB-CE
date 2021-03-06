## Update script to upload course program enrolments table in local db
# Peter Ryan Nov 2018

import datetime as dt
import psycopg2
from sqlalchemy import (create_engine, orm)
import pandas as pd
import tabulate

import sys
sys.path.append('c:\\Peter\\GitHub\\CoB\\')

import general.RMIT_colours as rc
from general.sams_queries import *
from general.sams_helper_functions import *
from general.postgres_queries import (
  qry_create_table_course_location,
  qry_add_comment,
  qry_drop_table,
  qry_delete_after_term)


# Create connections
# create sams engine this is the connection to the oracle database
password_str = input("SAMS Password: ") ## Input password
sams_engine = return_sams_engine(password_str=password_str)

# create postgres engine this is the connection to the oracle database
postgres_user = 'pjryan'
postgres_host = 'localhost'
postgres_dbname = 'postgres'
postgres_pw = input("Postgres Password: ") ## Input password
engine_string = 'postgresql+psycopg2://{}:{}@{}/{}'.format(postgres_user,
                                                           postgres_pw,
                                                           postgres_host,
                                                           postgres_dbname)
postgres_engine = create_engine(engine_string)
postgres_con = postgres_engine.connect()

# input parameters
st_term = input("Update from Start term: ")
end_term = input("Update until End term: ")

# get data from sams
sams_qry = qry_course_program_enrolments(st_term=st_term, end_term=end_term)
print(sams_qry)
try:
  df = pd.read_sql(sql=sams_qry, con=sams_engine)
except:
  print(sams_qry)

print(len(df))

x = postgres_con.execute(qry_delete_after_term(schema='enrolments',
                                               table='tbl_course_program_pop',
                                               term_code=st_term),
                         )

#print(tabulate.tabulate(result_dataframe.iloc[:10], headers='keys'))

df.to_sql(name='tbl_course_program_pop',
          con=postgres_engine,
          schema='enrolments',
          if_exists='append',
          index=False
          )

# Add update statement to table description
date = dt.datetime.now().date()
qry_comment = """
COMMENT ON TABLE enrolments.tbl_course_program_pop
    IS 'Updated on {0} for {1} to {2}'
;
""".format(date.strftime('%d-%m-%Y'), st_term, end_term)

print(qry_comment)
trans = postgres_con.begin()
postgres_con.execute(qry_comment)
trans.commit()