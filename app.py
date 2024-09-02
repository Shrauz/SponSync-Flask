from flask import Flask

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///db.sqlite3"
app.config['SECRET_KEY'] = 'my_secret_key'

from models import *
db.init_app(app)

with app.app_context():
    db.create_all()
    admin = User.query.filter_by(username='admin').first()
    types = Types.query.all()
    if len(types) == 0:
        db.session.add(Types(name='admin'))
        db.session.add(Types(name='influencer'))
        db.session.add(Types(name='sponsor'))
        db.session.commit()
        
    if not admin:
        admin = User(username='admin',password='admin',type='admin')
        db.session.add(admin)
        db.session.commit()

from routes import *

if __name__ == "__main__":
    app.run(debug=True)