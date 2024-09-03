from flask import render_template,redirect,request,url_for,flash,session
import re
import datetime
from datetime import date
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')
import io
import base64

from functools import wraps
from app import app
from models import Types,User,Sponsor,Influencer,Campaign,AdRequest,db

def create_graph(id):
    # Sample data from the database
    user = User.query.get(id)
    if user.type == 'admin':
        campaigns = Campaign.query.all()
    else:
        campaigns = Campaign.query.filter_by(sponsor_id=id).all()
    if campaigns:
        campaign_names = [campaign.name for campaign in campaigns]
        budgets = [campaign.budget for campaign in campaigns]

        # Generate the plot
        colors = ["#FABC3F","#E85C0D","#C7253E","#821131"]
        fig, ax = plt.subplots()
        ax.bar(campaign_names, budgets ,color = colors)
        ax.set_xlabel('Campaigns')
        ax.set_ylabel('Budget')
        ax.set_title('Campaign Budgets')

        # Save the plot to a BytesIO object
        img = io.BytesIO()
        plt.savefig(img, format='png')
        img.seek(0)

        # Convert the BytesIO object to a base64 string
        graph_url = base64.b64encode(img.getvalue()).decode()
        return f'data:image/png;base64,{graph_url}'
    else:
        return ""


def generate_user_type_pie_chart():
    plt.switch_backend('Agg')  # Use the 'Agg' backend for generating images
    
    # Get the counts of each user type excluding "admin"
    user_types = db.session.query(User.type, db.func.count(User.id)).filter(User.type != 'admin').group_by(User.type).all()
    
    # Extract the user type names and their counts
    labels = [user_type[0] for user_type in user_types]
    sizes = [user_type[1] for user_type in user_types]
    
    # Generate the pie chart
    fig, ax = plt.subplots(figsize=(4, 4))
    ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=140, colors=['#ff9999','#66b3ff','#99ff99','#ffcc99'])
    ax.axis('equal')  # Equal aspect ratio ensures the pie chart is circular.

    # Save the plot to a string in base64 format
    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    graph_url = base64.b64encode(img.getvalue()).decode()
    plt.close(fig)

    return f"data:image/png;base64,{graph_url}"

def auth_required(func):
    @wraps(func)
    def inner(*args , **kwargs):
        if 'user_id' not in session:
            flash('You need to login first.')
            return redirect(url_for('login'))
        return func(*args,**kwargs)
    return inner

@app.route('/')
def index():
    try:
        user = User.query.get(session['user_id'])
    except KeyError:
        return render_template('index.html')
    return render_template('index.html',user=user)


@app.route('/dashboard')
@auth_required
def dashboard():
    user = User.query.get(session['user_id'])
    if user.type == 'influencer':
        influencer = Influencer.query.get(user.id)
        return render_template('influencer.html',influencer=influencer,user=user)
    elif user.type == 'sponsor':
        campaigns = Campaign.query.all()
        graph_url = create_graph(user.id)
        sponsor = Sponsor.query.get(user.id)
        return render_template('sponsor.html',sponsor=sponsor,user=user,campaigns=campaigns,graph_url=graph_url)
    elif user.type == 'admin':
        graph_url = create_graph(user.id)
        pie_chart = generate_user_type_pie_chart()
        return render_template('admin.html',user = user,graph_url = graph_url,pie_chart = pie_chart)
    
@app.route('/login',methods = ['GET','POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username =='' or password == '':
            flash('Username or password cannot be empty')
            return redirect(url_for('register'))
        user = User.query.filter_by(username=username).first()
        if user :
            if user.password == password :
                if user.type == 'influencer':
                    influencer = Influencer.query.get(user.id)
                    if influencer.flagged == True:
                        flash('You are flagged ! You cannot Login.')
                        return redirect(url_for('login'))
                if user.type == 'sponsor':
                    sponsor = Sponsor.query.get(user.id)
                    if sponsor.flagged == True:
                        flash('You are flagged ! You cannot Login.')
                        return redirect(url_for('login'))
                flash('Login successful')
                session['user_id'] = user.id
                return redirect(url_for('dashboard'))
            else :
                flash('Wrong password')
                return redirect(url_for('login'))
        else :
            flash('User does not exist')
            return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/register',methods=['GET','POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        type = request.form.get('type')
        
        if username =='' or password == '':
            flash('Username or password cannot be empty')
            return redirect(url_for('register'))
    
        if User.query.filter_by(username=username).first():
            flash('User already exists')
            return redirect(url_for('register'))
        user = User(username=username, password=password,type=type)
        db.session.add(user)
        db.session.commit()
        if type == "influencer":
            return redirect(url_for('influencer_register',id=user.id))
        elif type == "sponsor":
            return redirect(url_for('sponsor_register',id=user.id))
    return render_template('register.html',types=Types.query.all())
        
@app.route('/influencer-register/<int:id>',methods=['GET','POST'])
def influencer_register(id):
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        category = request.form.get('category')
        niche = request.form.get('niche')
        platform = request.form.get('platform')
        followers = request.form.get('followers')
        influencer = Influencer(id=id,name=name,email=email,category=category,niche=niche,platform=platform,followers=followers)
        db.session.add(influencer)
        db.session.commit()
        flash('Influencer registered successfully ♥')
        return redirect(url_for('login'))
    return render_template('influencer-register.html',id=id)

@app.route('/sponsor-register/<int:id>',methods=['GET','POST'])
def sponsor_register(id):
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        company = request.form.get('company')
        industry = request.form.get('industry')
        sponsor = Sponsor(id=id,name=name,company=company,industry=industry,email=email)
        db.session.add(sponsor)
        db.session.commit()
        flash('Sponsor registered successfully ♥')
        return redirect(url_for('login'))
    return render_template('sponsor-register.html',id=id)

@app.route('/logout',methods=['GET','POST'])
@auth_required
def logout():
    user = User.query.get(session['user_id'])
    if (request.method == 'POST'):
        session.pop('user_id')
        flash('Logged out!')
        return redirect(url_for('index'))
    return render_template('logout.html',user=user)

@app.route('/campaign/add',methods=['GET','POST'])
@auth_required
def add_campaign():
    user = User.query.get(session['user_id'])
    if request.method == 'POST':
        id = user.id
        name = request.form.get('name')
        description = request.form.get('description')
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')
        budget = request.form.get('budget')
        visibility = request.form.get('visibility')
        if name == "":
            flash('Campaign name cannot be empty')
            return redirect(url_for('add_campaign'))
        if not re.match(r'^\d+(\.\d+)?$',budget):
            flash('Budget must be a number')
            return redirect(url_for('add_campaign'))
        budget = float(budget)
        try:
            start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d').date()
        except ValueError:
            flash('Start date is not in the correct format')
            return redirect(url_for('add_campaign'))
        
        try:
            end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d').date()
        except ValueError:
            flash('End date is not in the correct format')
        
        campaign = Campaign(name=name,sponsor_id=id,description=description,start_date=start_date,end_date=end_date,budget=budget,visibility=visibility)
        db.session.add(campaign)
        db.session.commit()
        flash('Campaign added successfully !')
        return redirect(url_for('sponsor_campaigns',user=user))
    return render_template('campaign/add.html',user=user,current_date = datetime.datetime.now().strftime("%Y-%m-%d"))

@app.route('/campaign/<int:id>/delete',methods=['GET','POST'])
@auth_required
def delete_campaign(id):
    campaign = Campaign.query.get(id)
    if request.method == 'POST':
        if not campaign:
            flash('Campaign does not exist')
            return redirect(url_for('dashboard'))
        for ad in (AdRequest.query.filter_by(campaign_id = campaign.id)):
            db.session.delete(ad)
        db.session.delete(campaign)
        db.session.commit()
        flash('Campaign deleted !')
        return redirect(url_for('sponsor_campaigns'))
    return render_template('campaign/delete.html',user=User.query.get(session['user_id']),campaign=campaign)

@app.route('/campaign/<int:id>/edit',methods=['GET','POST'])
@auth_required
def edit_campaign(id):
    user = User.query.get(session['user_id'])
    campaign = Campaign.query.get(id)
    if request.method == 'POST':
        
        if not campaign:
            flash('Campaign does not exist')
            return redirect(url_for('dashboard'))
        name = request.form.get('name')
        description = request.form.get('description')
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')
        budget = request.form.get('budget')
        visibility = request.form.get('visibility')
        if name == "":
            flash('Campaign name cannot be empty')
            return redirect(url_for('edit_campaign'))
        if not re.match(r'^\d+(\.\d+)?$',budget):
            flash('Budget must be a number')
            return redirect(url_for('edit_campaign'))
        budget = float(budget)
        try:
            start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d').date()
        except ValueError:
            flash('Start date is not in the correct format')
            return redirect(url_for('edit_campaign'))
        
        try:
            end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d').date()
        except ValueError:
            flash('End date is not in the correct format')
        
        campaign.name = name
        campaign.description = description
        campaign.start_date = start_date
        campaign.end_date = end_date
        campaign.budget = budget
        campaign.visibility = visibility
        
        db.session.commit()
        flash('Campaign edited successfully !')
        return redirect(url_for('sponsor_campaigns',user=user))
    return render_template('campaign/edit.html',user=user,campaign=campaign,current_date = date.today())

@app.route('/campaign/<int:id>/show')
@auth_required
def show_campaign(id):
    return render_template('campaign/show.html',campaign=Campaign.query.get(id),user=User.query.get(session['user_id']))

@app.route('/request/<int:id>/add',methods=['GET','POST'])
@auth_required
def add_request(id):
    user = User.query.get(session['user_id'])
    if request.method == 'POST':
        campaign_id = id
        requirements = request.form.get('requirements')
        payment = request.form.get('payment')
        if not re.match(r'^\d+(\.\d+)?$',payment):
            flash('Amount must be a number')
            return redirect(url_for('add_request'))
        payment = float(payment)
        adrequest = AdRequest(campaign_id=campaign_id,requirements=requirements,payment=payment)
        db.session.add(adrequest)
        db.session.commit()
        flash('Ad-request created successfully !')
        return redirect(url_for('show_campaign',id=id))
    return render_template('request/add.html',user=user)

@app.route('/request/<int:id>/delete',methods=['GET','POST'])
@auth_required
def delete_request(id):
    user = User.query.get(session['user_id'])
    adrequest = AdRequest.query.get(id)
    if request.method == 'POST':
        if not request:
            flash('Request not found')
        db.session.delete(adrequest)
        db.session.commit()
        flash('Ad-request deleted !')
        return redirect(url_for('show_campaign',id=adrequest.campaign_id))
    return render_template('request/delete.html',adrequest=adrequest,user=user)

@app.route('/request/<int:id>/done')
@auth_required
def done_request(id):
    adrequest = AdRequest.query.get(id)
    if not request:
        flash('Request not found')
    adrequest.status = "completed"
    db.session.commit()
    flash('Ad-request marked as done successfully !')
    return redirect(url_for('sponsor_ad_requests'))  
        

@app.route('/request/<int:id>/edit',methods=['GET','POST'])
@auth_required
def edit_request(id):
    user = User.query.get(session['user_id'])
    adrequest = AdRequest.query.get(id)
    if request.method == 'POST':
        requirements = request.form.get('requirements')
        payment = request.form.get('payment')
        status = request.form.get('status')
        influencer_id = request.form.get('influencer_id')
        influencer = Influencer.query.get(influencer_id)
        if influencer_id:
            if not influencer:
                flash('Influencer not found')
                return redirect(url_for('edit_request',id=id))
        if not re.match(r'^\d+(\.\d+)?$',payment):
            flash('Amount must be a number')
            return redirect(url_for('edit_request',id=id))
        payment = float(payment)
        adrequest.requirements = requirements
        adrequest.payment = payment
        adrequest.influencer_id = influencer_id
        adrequest.status = status
        db.session.commit()
        flash('Ad-request edited successfully !')
        return redirect(url_for('show_campaign',id=adrequest.campaign_id))
    return render_template('request/edit.html',user=user,ad=adrequest)


@app.route('/sponsor/ad_requests')
@auth_required
def sponsor_ad_requests():
    user = User.query.get(session['user_id'])
    sponsor = Sponsor.query.get(user.id)
    campaigns = Campaign.query.filter_by(sponsor_id = sponsor.id).all()
    ongoing_campaigns = Campaign.query.filter(
        Campaign.start_date <= date.today(),
        Campaign.end_date >= date.today()
    ).all()
    ongoing_campaign_ids = [campaign.id for campaign in ongoing_campaigns]
    ad_requests = AdRequest.query.filter(
        AdRequest.campaign_id.in_(ongoing_campaign_ids)
    ).all()
    return render_template('sponsor/ad_requests.html',user=user,sponsor=sponsor,campaigns=campaigns,ad_requests=ad_requests)

@app.route('/sponsor/campaigns')
@auth_required
def sponsor_campaigns():
    user = User.query.get(session['user_id'])
    sponsor = Sponsor.query.get(user.id)
    return render_template('sponsor/campaigns.html',user=user,sponsor=sponsor,campaigns=Campaign.query.all(),current_date = date.today())

@app.route('/sponsor/profile',methods=['GET','POST'])
@auth_required
def sponsor_profile():
    user = User.query.get(session['user_id'])
    sponsor = Sponsor.query.get(user.id)
    if request.method == 'POST':
        username = request.form.get('username')
        cpassword = request.form.get('cpassword')
        password = request.form.get('password')
        name = request.form.get('name')
        email = request.form.get('email')
        company = request.form.get('company')
        industry = request.form.get('industry')
        
        if cpassword == user.password:
            if user.username != username:
                if User.query.filter_by(username=username):
                    flash('User already exists')
                    return redirect(url_for('sponsor_profile'))
            else:
                user.username = username
                user.password = password
                sponsor.name = name
                sponsor.email = email
                sponsor.company = company
                sponsor.industry = industry
        
                db.session.commit()
                flash('Profile edited successfully ♥')
                return redirect(url_for('dashboard'))
        else:
            flash('Incorrect password')
            return redirect(url_for('sponsor_profile'))
        
       
    return render_template('sponsor/profile.html',user=user,sponsor=sponsor)

@app.route('/influencer/ad_requests')
@auth_required
def influencer_ad_requests():
    ongoing_campaigns = Campaign.query.filter(
        Campaign.start_date <= date.today(),
        Campaign.end_date >= date.today()
    ).all()
    ongoing_campaign_ids = [campaign.id for campaign in ongoing_campaigns]
    ad_requests = AdRequest.query.filter(
        AdRequest.campaign_id.in_(ongoing_campaign_ids)
    ).all()

    user = User.query.get(session['user_id'])
    influencer = Influencer.query.get(user.id)
    return render_template('influencer/ad_requests.html',user=user,influencer=influencer,ad_requests = ad_requests)

@app.route('/request/<int:id>/send')
@auth_required
def send_request(id):
    user = User.query.get(session['user_id'])
    adrequest = AdRequest.query.get(id)
    if not request:
        flash('Request not found')
    adrequest.influencer_id = user.id
    adrequest.status = "sent"
    db.session.commit()
    flash('Ad-request sent successfully !')
    return redirect(request.referrer)

@app.route('/request/<int:id>/accept')
@auth_required
def accept_request(id):
    user = User.query.get(session['user_id'])
    adrequest = AdRequest.query.get(id)
    if not request:
        flash('Request not found')
    adrequest.status = "accepted"
    db.session.commit()
    flash('Ad-request accepted successfully !')
    return redirect(request.referrer) 

@app.route('/request/<int:id>/reject')
@auth_required
def reject_request(id):
    user = User.query.get(session['user_id'])
    adrequest = AdRequest.query.get(id)
    if not request:
        flash('Request not found')
    adrequest.status = "rejected"
    db.session.commit()
    flash('Ad-request rejected !')
    return redirect(request.referrer) 

@app.route('/influencer/campaigns')
@auth_required
def influencer_campaigns():
    user = User.query.get(session['user_id'])
    influencer = Influencer.query.get(user.id)
    factor = request.args.get('factor')
    value = request.args.get('value')
    if factor == 'name':
        campaigns = Campaign.query.filter(Campaign.name.like('%' + value + '%')).all()
    elif factor == 'description':
        campaigns = Campaign.query.filter(Campaign.description.like('%' + value + '%')).all()
    elif factor == 'budget':
        value = float(value)
        campaigns = Campaign.query.filter(Campaign.budget >= value).all()
    else:
        campaigns = Campaign.query.all()
    return render_template('influencer/campaigns.html',user=user,influencer=influencer,campaigns=campaigns,current_date = date.today())


@app.route('/influencer/<int:id>/requests')
@auth_required
def show_requests(id):
    user = User.query.get(session['user_id'])
    influencer = Influencer.query.get(user.id)
    campaign = Campaign.query.get(id)
    sponsor = Sponsor.query.get(campaign.sponsor_id)
    ad_requests = AdRequest.query.filter_by(campaign_id = id).all()
    return render_template('influencer/show_requests.html',user=user,influencer=influencer,campaign=campaign,ad_requests=ad_requests,sponsor=sponsor)

@app.route('/influencer/profile',methods=['GET','POST'])
@auth_required
def influencer_profile():
    user = User.query.get(session['user_id'])
    influencer = Influencer.query.get(user.id)
    if request.method == 'POST':
        username = request.form.get('username')
        cpassword = request.form.get('cpassword')
        password = request.form.get('password')
        name = request.form.get('name')
        email = request.form.get('email')
        category = request.form.get('category')
        niche = request.form.get('niche')
        platform = request.form.get('platform')
        followers = request.form.get('followers')
        
        if cpassword == user.password:
            if user.username != username:
                if User.query.filter_by(username=username):
                    flash('User already exists')
                    return redirect(url_for('sponsor_profile'))
            else:
                user.username = username
                user.password = password
                influencer.name = name
                influencer.email = email
                influencer.category = category
                influencer.niche = niche
                influencer.platform = platform
                influencer.followers = followers
        
                db.session.commit()
                flash('Profile edited successfully ♥')
                return redirect(url_for('dashboard'))
        else:
            flash('Incorrect password')
            return redirect(url_for('influencer_profile'))
        
       
    return render_template('influencer/profile.html',user=user,influencer=influencer)

@app.route('/sponsor/<int:id>/influencers')
@auth_required
def find_influencers(id):
    user = User.query.get(session['user_id'])
    sponsor = Sponsor.query.get(user.id)
    factor = request.args.get('factor')
    adrequest = AdRequest.query.get(id)
    value = request.args.get('value')
    if factor == 'name':
        influencers = Influencer.query.filter(Influencer.name.like('%' + value + '%')).all()
    elif factor == 'category':
        influencers = Influencer.query.filter(Influencer.category.like('%' + value + '%')).all()
    elif factor == 'niche':
        influencers = Influencer.query.filter(Influencer.niche.like('%' + value + '%')).all()
    elif factor == 'platform':
        influencers = Influencer.query.filter(Influencer.platform.like('%' + value + '%')).all()
    elif factor == 'followers':
        value = int(value)
        influencers = Influencer.query.filter(Influencer.followers >= value).all()  
    else:
        influencers = Influencer.query.all()
    return render_template('sponsor/influencers.html',user=user,sponsor=sponsor,adrequest=adrequest,influencers=influencers,value=value)

@app.route('/request/<int:id>/recieve/<int:inf>')
@auth_required
def send_request_influencer(id,inf):
    adrequest = AdRequest.query.get(id)
    if not request:
        flash('Request not found')
    adrequest.influencer_id = inf
    adrequest.status = "recieved"
    db.session.commit()
    flash('Ad-request sent successfully !')
    return redirect(url_for('sponsor_ad_requests'))
    
@app.route('/admin/sponsors')
def admin_sponsors():
    user = User.query.get(session['user_id'])
    sponsors = Sponsor.query.all()
    return render_template('admin/sponsors.html',sponsors=sponsors,user=user)

@app.route('/admin/influencers')
def admin_influencers():
    user = User.query.get(session['user_id'])
    influencers = Influencer.query.all()
    return render_template('admin/influencers.html',influencers=influencers,user=user)

@app.route('/admin/campaigns')
def admin_campaigns():
    user = User.query.get(session['user_id'])
    campaigns = Campaign.query.all()
    return render_template('admin/campaigns.html',campaigns=campaigns,user=user,current_date=date.today())


@app.route('/flag/<int:id>/campaign')
@auth_required
def flag_campaign(id):
    campaign = Campaign.query.get(id)
    if not campaign:
        flash('Campaign not found')
    campaign.flagged = True
    db.session.commit()
    flash('Campaign flagged!')
    return redirect(request.referrer) 

@app.route('/unflag/<int:id>/campaign')
@auth_required
def unflag_campaign(id):
    campaign = Campaign.query.get(id)
    if not campaign:
        flash('Campaign not found')
    campaign.flagged = False
    db.session.commit()
    flash('Campaign un-flagged successfully!')
    return redirect(request.referrer) 

@app.route('/flag/<int:id>/user')
@auth_required
def flag_user(id):
    user = User.query.get(id)
    if not user:
        flash('User not found')
    if user.type == 'influencer':
        influnecer = Influencer.query.get(id)
        influnecer.flagged = True
    elif user.type == 'sponsor':
        sponsor = Sponsor.query.get(id)
        sponsor.flagged = True
    db.session.commit()
    flash('User flagged!')
    return redirect(request.referrer) 

@app.route('/unflag/<int:id>/user')
@auth_required
def unflag_user(id):
    user = User.query.get(id)
    if not user:
        flash('User not found')
    if user.type == 'influencer':
        influencer = Influencer.query.get(id)
        influencer.flagged = False
    elif user.type == 'sponsor':
        sponsor = Sponsor.query.get(id)
        sponsor.flagged = False
    db.session.commit()
    flash('User un-flagged successfully!')
    return redirect(request.referrer) 