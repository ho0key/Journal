from flask import Flask, render_template, request, redirect, url_for
import json
import os
from datetime import datetime, timedelta
import pandas as pd
import plotly
import plotly.graph_objs as go

app = Flask(__name__)
DATA_FILE = "doses.json"

# Elvanse effect percentages
effect_percent = [0,0,0,50,100,100,100,100,100,100,100,100,100,100,80,60,40,20,0]
time_step = 30
effect_duration = len(effect_percent) * time_step

# Load or initialize data
if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r") as f:
        saved_days = json.load(f)
else:
    saved_days = {"Day 1": []}

def save_data():
    with open(DATA_FILE, "w") as f:
        json.dump(saved_days, f)

def generate_graph(doses):
    if not doses:
        return None

    # Normalize all doses to a single reference date (today at 00:00)
    reference_date = datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)
    normalized_doses = [(dose, reference_date.replace(hour=dt.hour, minute=dt.minute)) for dose, dt in doses]

    # Determine full time range
    start_time = min(dt for _, dt in normalized_doses)
    end_time = max(dt + timedelta(minutes=effect_duration) for _, dt in normalized_doses)
    time_range = pd.date_range(start=start_time, end=end_time, freq=f"{time_step}min")
    combined_effect = pd.Series(0, index=time_range)

    print("DEBUG: normalized_doses:", normalized_doses)
    print("DEBUG: time_range:", time_range)

    # Apply effect_percent for each dose
    for dose, dt in normalized_doses:
        dose_scale = dose / 40  # scale effect by dose
        print(f"DEBUG: Applying dose {dose}mg at {dt.strftime('%H:%M')}, scale={dose_scale}")
        for i, perc in enumerate(effect_percent):
            effect_time = dt + timedelta(minutes=i*time_step)
            if effect_time > time_range[-1]:
                break
            pos = combined_effect.index.get_indexer([effect_time], method='nearest')[0]
            print(f"DEBUG: effect_time={effect_time}, perc={perc}, pos={pos}")
            combined_effect.iloc[pos] += perc * dose_scale

    print("DEBUG: combined_effect values:", combined_effect.values)
    # More debug about index types and sample
    if len(combined_effect.index) > 0:
        print("DEBUG: index[0] type:", type(combined_effect.index[0]), "repr:", repr(combined_effect.index[0]))
        sample_iso = [dt.isoformat() for dt in combined_effect.index[:10]]
        print("DEBUG: sample ISO x values:", sample_iso)

    # Create Plotly figure
    fig = go.Figure()
    # Serialize datetimes to ISO strings explicitly to avoid any client-side misinterpretation
    x_vals = [dt.isoformat() for dt in combined_effect.index]
    y_vals = combined_effect.values.tolist()
    print("DEBUG: x_vals length:", len(x_vals), "y_vals length:", len(y_vals))
    fig.add_trace(go.Scatter(
        x=x_vals,
        y=y_vals,
        mode='lines+markers',
        line=dict(color='cyan')
    ))
    # Configure layout: force date x-axis, tick every 30 minutes, remove grid
    thirty_min_ms = 30 * 60 * 1000
    tick0 = combined_effect.index[0].isoformat() if len(combined_effect.index) > 0 else None
    fig.update_layout(
        plot_bgcolor='#121212',
        paper_bgcolor='#121212',
        font_color='white',
        title='Combined Effect of Elvanse Doses',
        xaxis=dict(
            title='Time',
            type='date',
            tickmode='linear',
            tick0=tick0,
            dtick=thirty_min_ms,
            tickformat='%H:%M',
            tickangle=-45,
            showgrid=False
        ),
        yaxis=dict(
            title='Effect (%)',
            showgrid=False
        )
    )
    fig_json = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    print("DEBUG: fig_json preview:", fig_json[:400])
    return fig_json

@app.route("/")
def index():
    current_day = sorted(saved_days.keys())[0]
    doses = [(d[0], datetime.strptime(d[1], "%H:%M")) for d in saved_days[current_day]]
    graph_json = generate_graph(doses)
    return render_template("index.html", days=sorted(saved_days.keys()), current_day=current_day,
                           doses=doses, graph_json=graph_json)

@app.route("/load_day/<day_name>")
def load_day(day_name):
    doses = [(d[0], datetime.strptime(d[1], "%H:%M")) for d in saved_days[day_name]]
    graph_json = generate_graph(doses)
    return render_template("index.html", days=sorted(saved_days.keys()), current_day=day_name,
                           doses=doses, graph_json=graph_json)

@app.route("/new_day")
def new_day():
    next_day_index = len(saved_days) + 1
    day_name = f"Day {next_day_index}"
    saved_days[day_name] = []
    save_data()
    return redirect(url_for('load_day', day_name=day_name))

@app.route("/add_dose", methods=["POST"])
def add_dose():
    day_name = request.args.get("day")
    if not day_name:
        day_name = sorted(saved_days.keys())[-1]  # default to last day

    time_str = request.form.get("time")
    dose_amount = float(request.form.get("dose"))

    dt = datetime.strptime(time_str, "%H:%M")
    saved_days[day_name].append([dose_amount, time_str])
    save_data()
    return redirect(url_for("load_day", day_name=day_name))

@app.route("/delete_dose", methods=["POST"])
def delete_dose():
    day_name = request.args.get("day")
    if not day_name:
        day_name = sorted(saved_days.keys())[-1]

    time_str = request.form.get("time")
    dose_amount = float(request.form.get("dose"))

    saved_days[day_name] = [d for d in saved_days[day_name] if not (d[0]==dose_amount and d[1]==time_str)]
    save_data()
    return redirect(url_for("load_day", day_name=day_name))

if __name__ == "__main__":
    # Bind to 0.0.0.0 so devices on the same Wi-Fi can access the dev server.
    # Warning: this exposes the dev server on your LAN; don't use on untrusted networks.
    app.run(debug=True, host='0.0.0.0', port=5000)
