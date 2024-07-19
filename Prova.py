from datetime import date
from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, Date, Float, Time, CheckConstraint, ForeignKey, func
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
    Descrizione = db.Column(db.String(2047))
    Prezzo = db.Column(db.Float, nullable=False)
    Quantità = db.Column(db.Integer, nullable=False)
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
    
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def buyer_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        # Controlla se l'utente è un acquirente
        buyer = Acquirenti.query.filter_by(Id_Utente=session['user_id']).first()
        if not buyer:
            # Se non è un acquirente, controlla se è un venditore
            seller = Venditori.query.filter_by(Utente=session['user_id']).first()
            if seller:
                # Se è un venditore, reindirizza alla home del venditore
                return redirect(url_for('home_seller'))
            else:
                # Se non è né acquirente né venditore, reindirizza alla home generale
                return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

def seller_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        # Controlla se l'utente è un venditore
        seller = Venditori.query.filter_by(Utente=session['user_id']).first()
        if not seller:
            # Se non è un venditore, controlla se è un acquirente
            buyer = Acquirenti.query.filter_by(Id_Utente=session['user_id']).first()
            if buyer:
                # Se è un acquirente, reindirizza alla home dell'acquirente
                return redirect(url_for('home_buyer'))
            else:
                # Se non è né acquirente né venditore, reindirizza alla home generale
                return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

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
                session['user_surname'] = user.Cognome
                session['user_password'] = user.Password
                session['user_phone'] = user.Telefono
                session['user_address'] = user.Indirizzo

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
@login_required
def logout():
    seller = Venditori.query.filter_by(Utente=session['user_id']).first()
    if seller:
        session.pop('user_shop', None)
    session.pop('user_id', None)
    session.pop('user_email', None)
    session.pop('user_name', None)
    session.pop('user_surname', None)
    session.pop('user_password', None)
    session.pop('user_phone', None)
    session.pop('user_address', None)
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

@app.route('/home_buyer')
@buyer_required
def home_buyer():
    return render_template('home_buyer.html')

@app.route('/home_seller')
@seller_required
def home_seller():
    return render_template('home_seller.html')

#Impostazioni profilo
@app.route('/settings')
@login_required
def settings():
    return render_template('settings.html')

@app.route('/update_profile', methods=['POST'])
@login_required
def update_profile():
    user_id = session['user_id']
    user = Utenti.query.get(user_id)
    user.Nome = request.form['name']
    user.Cognome = request.form['surname']
    user.Email = request.form['email']
    user.Telefono = request.form['phone']
    user.Indirizzo = request.form['address']
    
    if 'user_shop' in session:
        shop = Venditori.query.filter_by(Utente=user_id).first()
        shop.Nome_Negozio = request.form['shop']
    
    db.session.commit()
    flash('Dati del profilo aggiornati con successo.', 'success')
    return redirect(url_for('settings'))

@app.route('/change_password', methods=['POST'])
@login_required
def change_password():
    user_id = session['user_id']
    user = Utenti.query.get(user_id)
    
    current_password = request.form['current_password']
    new_password = request.form['new_password']
    confirm_password = request.form['confirm_password']
    
    if not check_password_hash(user.Password, current_password):
        flash('La password corrente non è corretta.', 'error')
        return redirect(url_for('settings'))
    
    if new_password != confirm_password:
        flash('Le nuove password non sono uguali.', 'error')
        return redirect(url_for('settings'))
    
    user.Password = generate_password_hash(new_password)
    db.session.commit()
    flash('Password aggiornata correttamente.', 'success')
    return redirect(url_for('settings'))

#Nella Home del venditore
@app.route('/view_products')
@seller_required
def view_products():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    products = db.session.query(
        Prodotti,
        func.avg(Recensioni.Valutazione).label('media_valutazioni')
    ).outerjoin(Recensioni, Recensioni.Prodotto == Prodotti.Id_Prodotto)\
    .filter(Prodotti.Venditore == user_id)\
    .group_by(Prodotti.Id_Prodotto).all()
    return render_template('view_products.html', prodotti=products)

@app.route('/add_product', methods=['GET', 'POST'])
@seller_required
def add_product():
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        price = float(request.form['price'])
        quantity = int(request.form['quantity'])
        category = request.form['category']
        image_url = request.form['image_url']
        venditore = session['user_id']
        
        new_product = Prodotti(
            Nome_Prodotto=name,
            Descrizione=description,
            Prezzo=price,
            Quantità=quantity,
            Categoria=category,
            URL_Immagine=image_url,
            Venditore=venditore
        )
        
        db.session.add(new_product)
        db.session.commit()
        flash('Prodotto aggiunto con successo.', 'success')
        return redirect(url_for('view_products'))
    
    return render_template('add_product.html')

@app.route('/product_reviews/<int:product_id>')
@seller_required
def product_reviews(product_id):
    user_id = session['user_id']
    # Recupero i dettagli del prodotto
    product = Prodotti.query.filter_by(Id_Prodotto=product_id, Venditore=user_id).first()
    # Recupero le recensioni per il prodotto desiderato
    reviews = Recensioni.query.filter_by(Prodotto=product_id).all()
    
    return render_template('product_reviews.html', product=product, reviews=reviews)

@app.route('/edit_product/<int:id>', methods=['GET', 'POST'])
@seller_required
def edit_product(id):
    product = Prodotti.query.get_or_404(id)
    
    if request.method == 'POST':
        product.Nome_Prodotto = request.form['name']
        product.Descrizione = request.form['description']
        product.Prezzo = float(request.form['price'])
        product.Quantità = int(request.form['quantity'])
        product.Categoria = request.form['category']
        product.URL_Immagine = request.form['image_url']
        
        db.session.commit()
        flash('Prodotto aggiornato con successo.', 'success')
        return redirect(url_for('view_products'))
    
    return render_template('edit_product.html', product=product)

@app.route('/delete_product/<int:id>')
@seller_required
def delete_product(id):
    product = Prodotti.query.get_or_404(id)
    db.session.delete(product)
    db.session.commit()
    flash('Prodotto eliminato con successo.', 'success')
    return redirect(url_for('view_products'))

@app.route('/view_orders')
@seller_required
def view_orders():
    user_id = session['user_id']
    orders = Ordini.query.filter_by(Acquirente=user_id).all()
    return render_template('view_orders.html', ordini=orders)

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)


    