from flask_sqlalchemy import SQLAlchemy
db = SQLAlchemy()

class Types(db.Model):
    name = db.Column(db.String(30),primary_key=True)
    users = db.relationship("User",backref='type_of_users')
    

class User(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    username = db.Column(db.String(30),unique=True,nullable=False)
    password = db.Column(db.String(30),nullable=False)
    type = db.Column(db.String,db.ForeignKey("types.name"))
    
class Sponsor(db.Model):
    id = db.Column(db.Integer,db.ForeignKey("user.id"),primary_key=True)
    name = db.Column(db.String(30),nullable=False)
    company = db.Column(db.String(30),nullable=False)
    industry = db.Column(db.String(30),nullable=False)
    email = db.Column(db.String(30))
    flagged = db.Column(db.Boolean,nullable=False,default=False)
    
class Influencer(db.Model):
    id = db.Column(db.Integer,db.ForeignKey("user.id"),primary_key=True)
    name = db.Column(db.String(30),nullable=False)
    email = db.Column(db.String(30))
    category = db.Column(db.String(30),nullable=False)
    niche = db.Column(db.String(30),nullable=False)
    platform = db.Column(db.String(30),nullable=False)
    followers = db.Column(db.Integer,nullable=False)
    flagged = db.Column(db.Boolean,nullable=False,default=False)
    
class Campaign(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    name = db.Column(db.String(30),unique=True,nullable=False)
    sponsor_id = db.Column(db.Integer,db.ForeignKey("sponsor.id"))
    description = db.Column(db.String(1000),nullable=False)
    start_date = db.Column(db.Date,nullable=False)
    end_date = db.Column(db.Date,nullable=False)
    budget = db.Column(db.Float,nullable=False)
    visibility = db.Column(db.String(10),nullable=False)
    ad_requests = db.relationship("AdRequest",backref="campaign")
    flagged = db.Column(db.Boolean,nullable=False,default=False)
    
class AdRequest(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    campaign_id = db.Column(db.Integer,db.ForeignKey("campaign.id"))
    influencer_id = db.Column(db.Integer,db.ForeignKey("influencer.id"),nullable=True)
    status = db.Column(db.String(10),nullable=False,default="generated")
    payment = db.Column(db.Float,nullable=False)
    requirements = db.Column(db.String(100),nullable=False)
    
    