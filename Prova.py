from datetime import date
from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, Date, Float, Time, CheckConstraint, ForeignKey
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:21552155@localhost:5432/ECommerce'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.urandom(24)
db = SQLAlchemy(app)

class Utenti(db.Model):
    __tablename__ = 'utenti'
    Id_Utente = db.Column(db.Integer, primary_key=True)
    Nome = db.Column(db.String(255), nullable=False)
    Cognome = db.Column(db.String(255), nullable=False)
    Email = db.Column(db.String(255), nullable=False, unique=True)
    Telefono = db.Column(db.String(255), nullable=False)
    Password = db.Column(db.String(255), nullable=False)
    Data_Registrazione = db.Column(db.Date)
    Indirizzo = db.Column(db.String(255), nullable=False)

class Venditori(db.Model):
    __tablename__ = 'venditori'
    Utente = db.Column(db.Integer, db.ForeignKey('utenti.Id_Utente'), primary_key=True)
    Nome_Negozio = db.Column(db.String(255), nullable=False)

class Acquirenti(db.Model):
    __tablename__ = 'acquirenti'
    Id_Utente = db.Column(db.Integer, db.ForeignKey('utenti.Id_Utente'), primary_key=True)

class Prodotti(db.Model):
    __tablename__ = 'prodotti'
    Id_Prodotto = db.Column(db.Integer, primary_key=True)
    Nome_Prodotto = db.Column(db.String(255), nullable=False)
    Descrizione = db.Column(db.String(255))
    Prezzo = db.Column(db.Float, nullable=False)
    Quantità = db.Column(db.Float, nullable=False)
    Categoria = db.Column(db.String(255))
    URL_Immagine = db.Column(db.String(255))
    Venditore = db.Column(db.Integer, db.ForeignKey('venditori.Utente'))

class Carrelli(db.Model):
    __tablename__ = 'carrelli'
    Id_Carrello = db.Column(db.Integer, primary_key=True)
    Acquirente = db.Column(db.Integer, db.ForeignKey('acquirenti.Id_Utente'))

class Contiene(db.Model):
    __tablename__ = 'contiene'
    Carrello = db.Column(db.Integer, db.ForeignKey('carrelli.Id_Carrello'), primary_key=True)
    Prodotto = db.Column(db.Integer, db.ForeignKey('prodotti.Id_Prodotto'), primary_key=True)
    Quantità = db.Column(db.Integer, nullable=False)

class Ordini(db.Model):
    __tablename__ = 'ordini'
    Id_Ordine = db.Column(db.Integer, primary_key=True)
    Data_Ordine = db.Column(db.Date, nullable=False)
    Stato_Ordine = db.Column(db.String(255), nullable=False)
    db.CheckConstraint("Stato_Ordine IN ('In attesa', 'In corso', 'Consegnato')")
    Indirizzo_Spedizione = db.Column(db.String(255), nullable=False)
    Metodo_Pagamento = db.Column(db.String(255), nullable=False)
    Ora = db.Column(db.Time)
    Acquirente = db.Column(db.Integer, db.ForeignKey('acquirenti.Id_Utente'))

class Ordinato(db.Model):
    __tablename__ = 'ordinato'
    Ordine = db.Column(db.Integer, db.ForeignKey('ordini.Id_Ordine'), primary_key=True)
    Prodotto = db.Column(db.Integer, db.ForeignKey('prodotti.Id_Prodotto'), primary_key=True)
    Quantità = db.Column(db.Integer, nullable=False)

class Recensioni(db.Model):
    __tablename__ = 'recensioni'
    Id_Recensione = db.Column(db.Integer, primary_key=True)
    Valutazione = db.Column(db.Integer, nullable=False)
    db.CheckConstraint("Valutazione >= 1 AND Valutazione <= 5")
    Testo = db.Column(db.String(255))
    Data = db.Column(db.Date, nullable=False)
    Ora = db.Column(db.Time, nullable=False)
    Acquirente = db.Column(db.Integer, db.ForeignKey('acquirenti.Id_Utente'))
    Prodotto = db.Column(db.Integer, db.ForeignKey('prodotti.Id_Prodotto'))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = Utenti.query.filter_by(Email=email).first()

        if user:
            if check_password_hash(user.Password, password):
                session['user_id'] = user.Id_Utente
                session['user_email'] = user.Email
                session['user_name'] = user.Nome
                session['user_password'] = user.Password

                # Check if user is a seller or a buyer
                seller = Venditori.query.filter_by(Utente=user.Id_Utente).first()
                if seller:
                    session['user_shop'] = seller.Nome_Negozio
                    return redirect(url_for('home_seller'))
                else:
                    return redirect(url_for('home_buyer'))
            else:
                #in caso venga sbagliata la password
                flash('Password errata.', 'error')
                return render_template('login.html')
        else:
            #in caso la email non risulti registrata 
            flash('Email non trovata.', 'error')
            return render_template('login.html')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('user_email', None)
    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        surname = request.form['surname']
        email = request.form['email']
        phone = request.form['phone']
        password = request.form['password']
        data = date.today()
        address = request.form['address']
        user_type = request.form.get('user_type')
        shop = request.form.get('shop')
        
        # Controllo se la mail è già presente
        existing_user = Utenti.query.filter_by(Email=email).first()
        if existing_user:
            #in caso sia già presente l'email lancio il messaggio di errore
            flash('Email già registrata. Utilizza un indirizzo email diverso.', 'error')
            return render_template('register.html')
        else:
            hashed_password = generate_password_hash(password)
            new_user = Utenti(Nome=name, Cognome=surname, Email=email, Telefono=phone, Password=hashed_password, Data_Registrazione=data, Indirizzo=address)
            db.session.add(new_user)
            db.session.commit()

            if user_type == 'venditore':
                new_venditore = Venditori(Utente=new_user.Id_Utente, Nome_Negozio=shop)
                db.session.add(new_venditore)
            else:
                new_acquirente = Acquirenti(Id_Utente=new_user.Id_Utente)
                db.session.add(new_acquirente)

            db.session.commit()
            return redirect(url_for('index'))
    return render_template('register.html')

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/home_buyer')
@login_required
def home_buyer():
    return render_template('home_buyer.html')

@app.route('/home_seller')
@login_required
def home_seller():
    return render_template('home_seller.html')

@app.route('/settings')
@login_required
def settings():
    return render_template('settings.html')

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)


    