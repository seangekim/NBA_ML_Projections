# Sean Kim, sgkim@usc,edu
# ITP 216, Spring 2023
# Section: 31883
# Final Project
# Description: Creates sql DB storing nba stats from csv file

import sqlite3 as sl
import pandas as pd

db = "nba_stats.db"

def create_db():
    conn = sl.connect(db)
    curs = conn.cursor()
    stmt1 = ["CREATE TABLE nba_stats ('TEAM' TEXT, 'WIN%' FLOAT, 'SEASON' TEXT, '3P%' FLOAT)"]
    
    for stmt in stmt1:
        curs.execute(stmt)
    conn.commit()
    conn.close()

def store_db(fname, table):
    conn = sl.connect(db)
    curs = conn.cursor()
    file = open(fname, "r")

    pddb = pd.read_csv(fname, usecols=['TEAM', 'WIN%', 'SEASON', '3P%'])
    # delete this
    print('first 10 results')
    print(pddb.head(10))

    pddb.to_sql(name=table, con=conn, if_exists='replace')


    # delete this
    print('\nFirst 9 db results:')
    query = 'SELECT * FROM ' + table
    results = curs.execute(query).fetchmany(9)
    for result in results:
        print(result)

    conn.commit()
    conn.close()


def main():
    create_db()
    store_db("nba_stats.csv", "nba_stats")
    pass

if __name__ == "__main__":
    main()

    