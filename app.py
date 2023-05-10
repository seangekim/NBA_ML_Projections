# Sean Kim, sgkim@usc,edu
# ITP 216, Spring 2023
# Section: 31883
# Final Project
# Description: Shows NBA projected win rates data and previous win rates for a chosen team 
import io
import os
import sqlite3 as sl
import datetime

import pandas as pd
from flask import Flask, redirect, render_template, request, session, url_for, send_file
from matplotlib.figure import Figure
from sklearn.linear_model import LinearRegression

app = Flask(__name__)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
db = "nba_stats.db"


# home route 
@app.route("/")
def home():
    ss = {"past" : "Past Seasons",
          "projected" : "Projected Seasons"}

    return render_template("home.html", teams=db_get_teams(), message="Please enter an option to visualize.",
                           options=ss)


# route to submit a team
@app.route("/submit_team", methods=["POST"])
def submit_team():
    # session["team"] = request.form["team"].capitalize()
    print(request.form['team'])
    session["team"] = request.form["team"]
    if 'team' not in session or session["team"] == "":
        return redirect(url_for("home"))
    if "data_request" not in request.form:
        return redirect(url_for("home"))
    session["data_request"] = request.form["data_request"]
    return redirect(url_for("team_current", data_request=session["data_request"], team=session["team"]))


# route to return a render template with the appropriate selection from the user
@app.route("/api/nba_team/<data_request>/<team>")
def team_current(data_request, team):

    if data_request == "past":
        return render_template("past.html", data_request=data_request, team=team)
    else:
        return render_template("projected.html", data_request=data_request, team=team, project=False)

# submits a projection for the user
@app.route("/submit_projection", methods=["POST"])
def submit_projection():
    if 'team' not in session:
        return redirect(url_for("home"))
    session["SEASON"] = request.form["season"]
    # THESE NEED TO BE BACK IN!
    if session["team"] == "" or session["data_request"] == "" or session["SEASON"] == "":
 
        return redirect(url_for("home"))
    return redirect(url_for("team_projection", data_request=session["data_request"], team=session["team"]))


# route to create a team projection
@app.route("/api/nba_team/<data_request>/projection/<team>")
def team_projection(data_request, team):
    return render_template("projected.html", data_request=data_request, team=team, project=True, SEASON=session["SEASON"])


# creates a past figure 
@app.route("/past/<data_request>/<team>")
def fig(data_request, team):
    fig = create_figure(data_request,team)
    img = io.BytesIO()
    fig.savefig(img, format='png')
    img.seek(0)
    return send_file(img, mimetype="image/png")

# creates a figure for visualization
def create_figure(data_request, team):
    df = db_create_dataframe(data_request, team)
    print(session)

    # creates a past visualization
    if 'SEASON' not in session:
        print("past projection made")
        fig = Figure()
        ax = fig.add_subplot(1, 1, 1)
        fig.suptitle(data_request.capitalize() + " WIN% in " + team)
        ax.plot(df["SEASON"], df["WIN%"])
        ax.set(xlabel="SEASON", ylabel="Win Rate")
        return fig
    
    # creates a future visualization
    else:
        print("future projection made")
        df['SEASONMOD'] = [datetime.datetime(int(year), 1, 1) for year in df['SEASON']]
        y = df['WIN%'][-30:].values
        X = df['SEASONMOD'][-30:].values.reshape(-1, 1)
        # session['season'] = '11/11/20'  # REMOVE THIS LATER
        proj_year = int(session['SEASON'])
        dt = datetime.datetime(proj_year, 1, 1)
        
        draw = datetime.datetime(proj_year, 1, 1)

        regr = LinearRegression(fit_intercept=True, copy_X=True, n_jobs=2)
        regr.fit(X, y)
        projs = []
        
        # runs loop to create prediction for every year between now and proj_year
        print("entering loop")
        print("dt.year is ", str(dt.year))
        print("datetime is ", str(datetime.datetime.now().year+1))
        for year in range(datetime.datetime.now().year-4, dt.year):
            pred = int(regr.predict([[int(draw.timestamp())]])[0])
            print("SEASON IS ", str(year))
            print("WIN % is", pred)
            print("SEAsoN MOD IS ", draw)
            projs.append({"SEASON": int(year), "WIN%": pred, "SEASONMOD": draw})
            draw = draw.replace(year = year)
        print("leaving loop")
        # append() is removed in pandas 2.0, replace w/ concat() below

        # make a new dataframe for prediction
        print("the projs", projs) 
        print("end")
        df_pred = pd.DataFrame(projs)
        

        # save lengths of seasons and cases of original/historical data for diff colors below
        orig_season_len = len(df['SEASON'])
        orig_win_len = len(df['WIN%'])

        # concat orig and prediction dataframes
        df2 = pd.concat([df, df_pred])

        fig = Figure()
        ax = fig.add_subplot(1, 1, 1)
        fig.suptitle("Projected win rate for " + team + " until " + session["SEASON"])

        # show the original/historical data in blue using slicing
        ax.plot(df["SEASON"][:orig_season_len], df["WIN%"][:orig_win_len], color='blue', label="Previous Win Rates")
    
        # show the predicted data in orange, notice the - 1 since a line plot needs at least 2 points.
        print("OVER HERE DF2 ", df2)
        # ax.plot(pd.to_datetime(df2['SEASONMOD'])[orig_season_len - 1:], df2['WIN%'][orig_win_len - 1:], color='orange', label="Projected Win Rates")
        print("len of df is ", str(len(df)))
        ax.set(xlabel="Season", ylabel="WIN%")
        ax.set_xlim(left=2000)
        return fig

# creates a datafame based on the db with only the season and win percentagn
def db_create_dataframe(data_request, team):
    conn = sl.connect(db)
    curs = conn.cursor()

    df = pd.DataFrame()
    table = "nba_stats"
  
    stmt = "SELECT * from " + table + " where `TEAM`=?"

    df = pd.read_sql_query(stmt, conn, params=[team])
    df["SEASON"] = df["SEASON"].str.extract(r"(\d{4})-\d{2}")[0].astype(int)

    df = df[["SEASON", "WIN%"]]
    conn.close()
    return df


   

# returns a list of all the teams
def db_get_teams():
    conn = sl.connect(db)
    curs = conn.cursor()

    stmt = "SELECT `TEAM` from 'nba_stats'"
    data = curs.execute(stmt)
    # sort a set comprehension for unique values
    teams = sorted({result[0] for result in data})
    conn.close()
    return teams

# returns a list of all the valid seasons
def db_get_seasons():
    conn = sl.connect(db)
    curs = conn.cursor()

    stmt = "SELECT `SEASON` from 'nba_stats'"
    data = curs.execute(stmt)
    # sort a set comprehension for unique values
    seasons = sorted({result[0] for result in data})
    conn.close()
    return seasons


# catch all to route back to home page
@app.route('/<path:path>')
def catch_all(path):
    return redirect(url_for("home"))


if __name__ == "__main__":
    app.secret_key = os.urandom(12)
    app.run(debug=True)
