# Local imports
import random

# Third-party imports
from flask import render_template, redirect, url_for, flash, request, abort
from flask_login import login_user, current_user, logout_user, login_required

# Local imports
from tradelogger import app, db, bcrypt
from tradelogger.models import Users, Trades
from tradelogger.forms import RegistrationForm, LoginForm, NewLogForm
from tradelogger.helpers import myr
from tradelogger.ml_models import ml_prediction_sidebar_pipeline

def ai_says(pl_vals, total_trades):
    if not pl_vals:
        return "It seems that you have not trade anything yet."
    
    on_profit = ["Buy Low Sell High :)",
                 f"Seems like you are profiting recently. Remember not to overtrade {current_user.username}.",
                 "Have a trading plan.",
                 "Set your EP, TP and CL before making a trade!",
                 ]

    on_loss = [f"Your last trade was a loss, maybe take a break {current_user.username}?",
               "Sometimes, not trading is the best trade.",
               "Have a trading plan.",
               "Set your EP, TP and CL before making a trade!",
               "Try a different trading strategy, buy on dip, buy on rebound?"
               ]
    
    if pl_vals[-1] < 0 and total_trades % 100 == 0:
        ai_says_text = random.choice([f"Wow, you've reached {total_trades} trades already."] + on_loss)
    if pl_vals[-1] > 0 and total_trades % 100 == 0:
        ai_says_text = random.choice([f"Wow, you've reached {total_trades} trades already."] + on_profit)
    elif pl_vals[-1] < 0:
        ai_says_text = random.choice(on_loss)
    elif pl_vals[-1] > 0:
        ai_says_text = random.choice(on_profit)

    return ai_says_text


# Routes for web app
@app.route("/")
@app.route("/home")
@login_required
def index():
    page = request.args.get('page', 1, type=int)
    logs = Trades.query.filter_by(user_id=current_user.get_id()) \
                       .order_by(Trades.created_at.desc())
    
    # # Get recent logs from user
    # _query_recent_logs = 5
    # logs_recent = logs.limit(_query_recent_logs).all()
    
    # Get paginated logs from user
    logs_paginated = logs.paginate(per_page=10, page=page)
    
    # Total trades by user
    total_trades = Trades.query.filter_by(user_id=current_user.get_id()).count()

    trade_date_vals = []
    
    # Compute net profit of current users
    net_profit = 0
    pl_vals = []
    
    pl_query = Trades.query.filter_by(user_id=current_user.get_id())\
                           .with_entities(Trades.created_at, Trades.profit_loss)
                            
    for query in pl_query:
        pl = query[1]
        net_profit += pl
        pl_vals.append(float(pl))
        trade_date_vals.append(query[0])
    
    # df = pd.DataFrame(dict(dates=trade_date_vals, profit_loss=pl_vals))
        
    net_profit = round(net_profit/100., 2)
    
    # Next trade ML prediction
    trade_pred, monthly_pred = ml_prediction_sidebar_pipeline(trade_date_vals, pl_vals)
    
    # AI Says
    says = ai_says(pl_vals, total_trades)

    return render_template("index.html",
                           logs=logs_paginated,
                           total_trades=total_trades,
                           net_profit=net_profit,
                           ai_says=says,
                           next_trade_pred=trade_pred,
                           next_monthly_pred=monthly_pred)


@app.route("/register", methods=['GET', 'POST'])
def register():
    # Instantiate RegistrationForm
    form = RegistrationForm()

    # User reached register via POST
    if form.validate_on_submit():
        # Hash the password and instantiate user
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = Users(username=form.username.data, email=form.email.data, password=hashed_password)

        # Add and commit to database
        db.session.add(user)
        db.session.commit()
        
        # Flash user and redirect to login page
        flash(f"Your account has been created successfully! Please log in with your username and password.", 'success')

        return redirect(url_for('login'))
    
    # To return in layout.html
    total_trades = Trades.query.count()
    
    # Compute net profit of all users
    net_profit = 0
    pl_query = Trades.query.with_entities(Trades.profit_loss)
    for pl in pl_query:
        net_profit += pl[0]

    net_profit = round(net_profit / 100, 2)

    # User reached register via GET
    return render_template("register.html", title="Register", form=form, total_trades=total_trades, net_profit=net_profit)


@app.route("/login", methods=['GET', 'POST'])
def login():
    # Checks if current user is already logged in
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    # Instantiate LoginForm
    form = LoginForm()

    # User reached route via POST
    if form.validate_on_submit():
        user = Users.query.filter_by(username=form.username.data).first()

        # Check user exists and password matches
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            # Gets next page if login was triggered from accessing login-only pages
            next_page = request.args.get('next')
            # Returns next page if it exists
            if next_page:
                return redirect(next_page)
            else:
                flash(f"Login successful! Welcome back, {current_user.username}.", 'success')
                return redirect(url_for('index'))
        else:
            flash("Unsuccessful login. Please check username and password", 'danger')
    
    # Number of trades
    total_trades = Trades.query.count()

    # Compute net profit of all users
    net_profit = 0
    pl_query = Trades.query.with_entities(Trades.profit_loss)
    for pl in pl_query:
        net_profit += pl[0]

    net_profit = round(net_profit / 100, 2)

    # User reached route via GET
    return render_template("login.html", title="Login", form=form, total_trades=total_trades, net_profit=net_profit)


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route("/account")
@login_required
def account():
    return render_template("account.html", title="Account")

@app.route("/logs/new", methods=['GET', 'POST'])
@login_required
def new_log():
    form = NewLogForm()

    if form.validate_on_submit():
        
        # Compute profit loss approximation
        buy_price = round(form.buy_price.data, 2) * 100
        sell_price = round(form.sell_price.data, 2) * 100
        quantity = form.quantity.data
        # MAY NEED TO IMPROVE THIS FORMULA  
        profit_loss = int(quantity * 100 * (sell_price - buy_price))

        # Log the trade
        log = Trades(stock_name=form.stock_name.data.upper(),
                     buy_price=buy_price,
                     sell_price=sell_price,
                     quantity=quantity,
                     profit_loss=profit_loss,
                     sell_type=form.sell_type.data,
                     author=current_user)
        
        # Add the log, commit to database and update user
        db.session.add(log)
        db.session.commit()
        flash("Your log has been created!", 'success')

        return redirect(url_for('index'))

    # Total trades by user
    total_trades = Trades.query.filter_by(user_id=current_user.get_id()).count()
    
    trade_date_vals = []
    
    # Compute net profit of current users
    net_profit = 0
    pl_vals = []
    
    pl_query = Trades.query.filter_by(user_id=current_user.get_id())\
                           .with_entities(Trades.created_at, Trades.profit_loss)
                            
    for query in pl_query:
        pl = query[1]
        net_profit += pl
        pl_vals.append(float(pl))
        trade_date_vals.append(query[0])
    
    # df = pd.DataFrame(dict(dates=trade_date_vals, profit_loss=pl_vals))
        
    net_profit = round(net_profit/100., 2)
    
    # Next trade ML prediction
    trade_pred, monthly_pred = ml_prediction_sidebar_pipeline(trade_date_vals, pl_vals)

    # Some AI
    says = ai_says(pl_vals, total_trades)

    return render_template("create_log.html",
                           title="New Log",
                           form=form,
                           legend="New Log",
                           total_trades=total_trades,
                           net_profit=net_profit,
                           ai_says=says,
                           next_trade_pred=trade_pred,
                           next_monthly_pred=monthly_pred)

@app.route("/logs/<int:log_id>")
@login_required
def log(log_id):
    log = Trades.query.get_or_404(log_id)
    
    # Compute net profit of current users
    net_profit = 0
    pl_vals = []
    
    pl_query = Trades.query.filter_by(user_id=current_user.get_id())\
                           .with_entities(Trades.profit_loss)
    for pl in pl_query:
        net_profit += pl[0]
        pl_vals.append(pl[0])
        
    net_profit = round(net_profit / 100, 2)
    
    return render_template("log.html", log=log, net_profit=net_profit)

@app.route("/logs/<int:log_id>/update", methods=['GET', 'POST'])
@login_required
def update_log(log_id):
    log = Trades.query.get_or_404(log_id)
    if log.author != current_user:
        abort(403)

    form = NewLogForm()
    if form.validate_on_submit():
        log.stock_name = form.stock_name.data
        log.buy_price = form.buy_price.data
        log.sell_price = form.sell_price.data
        log.quantity = form.quantity.data
        log.sell_type = form.sell_type.data
        db.session.commit()
        flash("Your log has been updated!", 'success')
        return redirect(url_for('index'))
    
    elif request.method == 'GET':
        form.stock_name.data = log.stock_name
        form.buy_price.data = log.buy_price
        form.sell_price.data = log.sell_price
        form.quantity.data = log.quantity
        form.sell_type.data = log.sell_type

    # Total trades by user
    total_trades = Trades.query.filter_by(user_id=current_user.get_id()).count()
    
    # Compute net profit of current users
    net_profit = 0
    pl_vals = []
    
    pl_query = Trades.query.filter_by(user_id=current_user.get_id())\
                           .with_entities(Trades.profit_loss)
    for pl in pl_query:
        net_profit += pl[0]
        pl_vals.append(pl[0])
        
    net_profit = round(net_profit / 100, 2)

    # Some AI
    says = ai_says(pl_vals, total_trades)

    return render_template("create_log.html", title="Update Log", 
                           form=form, legend="Update Log", net_profit=net_profit, ai_says=says)


@app.route("/logs/<int:log_id>/delete", methods=['POST'])
@login_required
def delete_log(log_id):
    log = Trades.query.get_or_404(log_id)
    if log.author != current_user:
        abort(403)
    db.session.delete(log)
    db.session.commit()
    flash("Your log has been deleted!", 'success')
    return redirect(url_for('index'))
