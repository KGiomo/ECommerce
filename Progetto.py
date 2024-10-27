'''
Data di creazione: 15-7-2024
Ultima modifica: 20-9-2024
'''

from datetime import date, datetime
from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, Date, Float, Time, CheckConstraint, ForeignKey, func
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:yourpostgrespassword@localhost:5432/ECommerce'
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
    
    venditori = db.relationship('Venditori', backref='utente', cascade="all, delete-orphan", passive_deletes=True)
    acquirenti = db.relationship('Acquirenti', backref='utente', cascade="all, delete-orphan", passive_deletes=True)

class Venditori(db.Model):
    __tablename__ = 'venditori'
    Utente = db.Column(db.Integer, db.ForeignKey('utenti.Id_Utente', ondelete='CASCADE'), primary_key=True)
    Nome_Negozio = db.Column(db.String(255), nullable=False)
    
    prodotti = db.relationship('Prodotti', backref='venditore', cascade="all, delete-orphan", passive_deletes=True)

class Acquirenti(db.Model):
    __tablename__ = 'acquirenti'
    Id_Utente = db.Column(db.Integer, db.ForeignKey('utenti.Id_Utente', ondelete='CASCADE'), primary_key=True)
    
    carrelli = db.relationship('Carrelli', backref='acquirente', cascade="all, delete-orphan", passive_deletes=True)
    ordini = db.relationship('Ordini', backref='acquirente', cascade="all, delete-orphan", passive_deletes=True)
    recensioni = db.relationship('Recensioni', backref='acquirente', cascade="all, delete-orphan", passive_deletes=True)

class Prodotti(db.Model):
    __tablename__ = 'prodotti'
    Id_Prodotto = db.Column(db.Integer, primary_key=True)
    Nome_Prodotto = db.Column(db.String(255), nullable=False)
    Descrizione = db.Column(db.String(2047))
    Prezzo = db.Column(db.Float, nullable=False)
    Quantità = db.Column(db.Integer, nullable=False)
    Categoria = db.Column(db.String(255))
    URL_Immagine = db.Column(db.String(255))
    Venditore = db.Column(db.Integer, db.ForeignKey('venditori.Utente', ondelete='CASCADE'))
    
    contiene = db.relationship('Contiene', backref='prodotto', cascade="all, delete-orphan", passive_deletes=True)
    ordinato = db.relationship('Ordinato', backref='prodotto', cascade="all, delete-orphan", passive_deletes=True)
    recensioni = db.relationship('Recensioni', backref='prodotto', cascade="all, delete-orphan", passive_deletes=True)

class Carrelli(db.Model):
    __tablename__ = 'carrelli'
    Id_Carrello = db.Column(db.Integer, primary_key=True)
    Acquirente = db.Column(db.Integer, db.ForeignKey('acquirenti.Id_Utente', ondelete='CASCADE'))
    
    contiene = db.relationship('Contiene', backref='carrello', cascade="all, delete-orphan", passive_deletes=True)

class Contiene(db.Model):
    __tablename__ = 'contiene'
    Carrello = db.Column(db.Integer, db.ForeignKey('carrelli.Id_Carrello', ondelete='CASCADE'), primary_key=True)
    Prodotto = db.Column(db.Integer, db.ForeignKey('prodotti.Id_Prodotto', ondelete='CASCADE'), primary_key=True)
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
    Acquirente = db.Column(db.Integer, db.ForeignKey('acquirenti.Id_Utente', ondelete='CASCADE'))
    
    ordinato = db.relationship('Ordinato', backref='ordine', cascade="all, delete-orphan", passive_deletes=True)

class Ordinato(db.Model):
    __tablename__ = 'ordinato'
    Ordine = db.Column(db.Integer, db.ForeignKey('ordini.Id_Ordine', ondelete='CASCADE'), primary_key=True)
    Prodotto = db.Column(db.Integer, db.ForeignKey('prodotti.Id_Prodotto', ondelete='CASCADE'), primary_key=True)
    Quantità = db.Column(db.Integer, nullable=False)

class Recensioni(db.Model):
    __tablename__ = 'recensioni'
    Id_Recensione = db.Column(db.Integer, primary_key=True)
    Valutazione = db.Column(db.Integer, nullable=False)
    db.CheckConstraint("Valutazione >= 1 AND Valutazione <= 5")
    Titolo = db.Column(db.String(255))
    Testo = db.Column(db.String(2047))
    Data = db.Column(db.Date, nullable=False)
    Acquirente = db.Column(db.Integer, db.ForeignKey('acquirenti.Id_Utente', ondelete='CASCADE'))
    Prodotto = db.Column(db.Integer, db.ForeignKey('prodotti.Id_Prodotto', ondelete='CASCADE'))

    
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
        # SELECT * FROM Utenti WHERE Email = 'email' LIMIT 1;
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

                # Controlla se l'utente è un venditore oppure un acquirente
                # SELECT * FROM Venditori WHERE Utente = user_id LIMIT 1;
                seller = Venditori.query.filter_by(Utente=user.Id_Utente).first()
                if seller:
                    session['user_shop'] = seller.Nome_Negozio
                    return redirect(url_for('home_seller'))
                else:
                    return redirect(url_for('home_buyer'))
            else:
                # In caso venga sbagliata la password
                flash('Password errata.', 'error')
                return render_template('login.html')
        else:
            # In caso la email non risulti registrata 
            flash('Email non trovata.', 'error')
            return render_template('login.html')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    #SELECT * FROM Venditori WHERE Utente = session_user_id LIMIT 1;
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
        repassword = request.form['repassword']
        data = date.today()
        address = request.form['address']
        user_type = request.form.get('user_type')
        shop = request.form.get('shop')
        
        # Controllo se la mail è già presente
        existing_user = Utenti.query.filter_by(Email=email).first()
        if existing_user:
            # In caso sia già presente l'email lancio il messaggio di errore
            flash('Email già registrata. Utilizza un indirizzo email diverso.', 'error')
            return render_template('register.html')
        elif password != repassword:
            # In caso sia le due password inserite non coincidano
            flash('Le due Password non corrispondono.', 'error')
            return render_template('register.html')
        else:
            hashed_password = generate_password_hash(password)
            new_user = Utenti(Nome=name, Cognome=surname, Email=email, Telefono=phone, Password=hashed_password, Data_Registrazione=data, Indirizzo=address)
            db.session.add(new_user)
            db.session.commit()

            if user_type == 'venditore':
                # INSERT INTO Venditori (Utente, Nome_Negozio) VALUES (new_user_id, 'shop_name');
                new_venditore = Venditori(Utente=new_user.Id_Utente, Nome_Negozio=shop)
                db.session.add(new_venditore)
            else:
                # INSERT INTO Acquirenti (Id_Utente) VALUES (new_user_id);
                new_acquirente = Acquirenti(Id_Utente=new_user.Id_Utente)
                db.session.add(new_acquirente)
                # Crea il carrello per il nuovo utente
                #INSERT INTO carrelli (Acquirente) VALUES (new_user_id);
                new_carrello = Carrelli(Acquirente=new_user.Id_Utente)
                db.session.add(new_carrello)

            db.session.commit()
            return redirect(url_for('index'))
    return render_template('register.html')

# Impostazioni profilo
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
        # SELECT * FROM Venditori WHERE Utente = user_id LIMIT 1;
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

# Metodi che riguardano il venditore
@app.route('/home_seller')
@seller_required
def home_seller():
    return render_template('home_seller.html')

@app.route('/view_products')
@seller_required
def view_products():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    """SELECT Prodotti.*, AVG(Recensioni.Valutazione) AS media_valutazioni
    FROM Prodotti LEFT JOIN Recensioni ON Recensioni.Prodotto = Prodotti.Id_Prodotto
    WHERE Prodotti.Venditore = user_id
    GROUP BY Prodotti.Id_Prodotto;"""
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
        return redirect(url_for('view_products'))
    
    return render_template('add_product.html')

@app.route('/product_reviews/<int:product_id>')
@seller_required
def product_reviews(product_id):
    user_id = session['user_id']
    # SELECT * FROM Prodotti WHERE Id_Prodotto = product_id AND Venditore = user_id LIMIT 1;
    prodotto = Prodotti.query.filter_by(Id_Prodotto=product_id, Venditore=user_id).first()
    order = request.args.get('order', 'recent')  # Di default 'recent'
    
    # SELECT * FROM Recensioni WHERE Prodotto = product_id ORDER BY order;
    if order == 'recent':
        recensioni = Recensioni.query.filter_by(Prodotto=product_id).order_by(Recensioni.Data.desc()).all()
    elif order == 'oldest':
        recensioni = Recensioni.query.filter_by(Prodotto=product_id).order_by(Recensioni.Data.asc()).all()
    elif order == 'highest_rating':
        recensioni = Recensioni.query.filter_by(Prodotto=product_id).order_by(Recensioni.Valutazione.desc()).all()
    elif order == 'lowest_rating':
        recensioni = Recensioni.query.filter_by(Prodotto=product_id).order_by(Recensioni.Valutazione.asc()).all()
    else:
        recensioni = Recensioni.query.filter_by(Prodotto=product_id).order_by(Recensioni.Data.desc()).all()
    
    return render_template('product_reviews.html', prodotto=prodotto, recensioni=recensioni)


@app.route('/edit_product/<int:id>', methods=['GET', 'POST'])
@seller_required
def edit_product(id):
    # SELECT * FROM Prodotti WHERE Id_Prodotto = id;
    # Genera un errore 404 se il prodotto non viene trovato nel database
    product = Prodotti.query.get_or_404(id)
    
    if request.method == 'POST':
        product.Nome_Prodotto = request.form['name']
        product.Descrizione = request.form['description']
        product.Prezzo = float(request.form['price'])
        product.Quantità = int(request.form['quantity'])
        product.Categoria = request.form['category']
        product.URL_Immagine = request.form['image_url']
        
        db.session.commit()
        return redirect(url_for('view_products'))
    
    return render_template('edit_product.html', product=product)

@app.route('/delete_product/<int:id>')
@seller_required
def delete_product(id):
    # SELECT * FROM Prodotti WHERE Id_Prodotto = id;
    # Genera un errore 404 se il prodotto non viene trovato nel database
    product = Prodotti.query.get_or_404(id)
    db.session.delete(product)
    db.session.commit()

    return redirect(url_for('view_products'))

@app.route('/view_orders', methods=['GET', 'POST'])
@seller_required
def view_orders():
    user_id = session['user_id']
    stato_ordine = request.args.get('stato_ordine')
    order_by = request.args.get('order_by', 'id')  # Default: ordina per ID
    
    # Query per ottenere gli ordini contenenti prodotti del venditore corrente
    '''SELECT Ordini.*, 
       Utenti.Nome AS Nome_Acquirente, 
       Utenti.Cognome AS Cognome_Acquirente
    FROM Ordini
    JOIN Acquirenti ON Ordini.Acquirente = Acquirenti.Id_Utente
    JOIN Utenti ON Acquirenti.Id_Utente = Utenti.Id_Utente
    JOIN Ordinato ON Ordini.Id_Ordine = Ordinato.Ordine
    JOIN Prodotti ON Ordinato.Prodotto = Prodotti.Id_Prodotto
    JOIN Venditori ON Prodotti.Venditore = Venditori.Utente
    WHERE Venditori.Utente = user_id;'''
    orders_query = db.session.query(Ordini, Utenti.Nome.label('Nome_Acquirente'), Utenti.Cognome.label('Cognome_Acquirente')) \
                             .join(Acquirenti, Ordini.Acquirente == Acquirenti.Id_Utente) \
                             .join(Utenti, Acquirenti.Id_Utente == Utenti.Id_Utente) \
                             .join(Ordinato, Ordini.Id_Ordine == Ordinato.Ordine) \
                             .join(Prodotti, Ordinato.Prodotto == Prodotti.Id_Prodotto) \
                             .join(Venditori, Prodotti.Venditore == Venditori.Utente) \
                             .filter(Venditori.Utente == user_id)  # Filtra per venditore
    
    # Prende orders_query e nel WHERE aggiunge la condizione AND Ordini.Stato_Ordine = 'stato_ordine';
    if stato_ordine:
        orders_query = orders_query.filter(Ordini.Stato_Ordine == stato_ordine)
    
    # Ordinare in base al criterio selezionato
    # Prende orders_query ed aggiunge ORDER BY Ordini.Data_Ordine order_by
    if order_by == 'recent':
        orders_query = orders_query.order_by(Ordini.Data_Ordine.desc())
    elif order_by == 'oldest':
        orders_query = orders_query.order_by(Ordini.Data_Ordine.asc())
    else:  # Default: ordina per ID
        orders_query = orders_query.order_by(Ordini.Id_Ordine.asc())
    
    # Esegue la query
    orders = orders_query.all()
    
    # Filtro aggiuntivo sui prodotti per venditore (Serve per far visualizzare al venditore solo i suoi prodotti presenti nei vari ordini)
    filtered_orders = []
    for ordine, Nome_Acquirente, Cognome_Acquirente in orders:
        prodotti_filtrati = [item for item in ordine.ordinato if item.prodotto.Venditore == user_id]
        if prodotti_filtrati:
            filtered_orders.append((ordine, Nome_Acquirente, Cognome_Acquirente, prodotti_filtrati))

    return render_template('view_orders.html', ordini=filtered_orders)


@app.route('/update_order_status/<int:ordine_id>', methods=['POST'])
@seller_required
def update_order_status(ordine_id):
    new_status = request.form['stato_ordine']
    print(new_status)
    ordine = Ordini.query.get(ordine_id)    
    if ordine:
        ordine.Stato_Ordine = new_status
        db.session.commit()  
    return redirect(url_for('view_orders'))

# Metodi che riguardano l'acquirente
@app.route('/home_buyer')
@buyer_required
def home_buyer():
    return render_template('home_buyer.html')

@app.route('/search_products', methods=['GET', 'POST'])
@buyer_required
def search_product():
    if request.method == 'POST':
        keyword = request.form.get('keyword', '')
        categoria = request.form.get('category', '')
        prezzo_min = request.form.get('min_price', 0)
        prezzo_max = request.form.get('max_price', None)
        venditore = request.form.get('seller', '')
        
        # Query per ottenere tutti i prodotti con la media dei voti delle relative recensioni
        '''SELECT Prodotti.*, 
            Venditori.Nome_Negozio, 
            AVG(Recensioni.Valutazione) AS media_valutazione
        FROM Prodotti
        LEFT JOIN Venditori ON Prodotti.Venditore = Venditori.Utente
        LEFT JOIN Recensioni ON Prodotti.Id_Prodotto = Recensioni.Prodotto
        GROUP BY Prodotti.Id_Prodotto, Venditori.Nome_Negozio;'''
        prodotti = db.session.query(
            Prodotti, 
            Venditori.Nome_Negozio,
            func.avg(Recensioni.Valutazione).label('media_valutazione')
        ).outerjoin(Venditori, Prodotti.Venditore == Venditori.Utente
        ).outerjoin(Recensioni, Prodotti.Id_Prodotto == Recensioni.Prodotto
        ).group_by(Prodotti.Id_Prodotto, Venditori.Nome_Negozio)

        # Filtraggio dei prodotti secondo i criteri scelti dall'utente
        # Alla query prodotti prima del GROUP BY è come se aggiungesse WHERE (condizioni inserite nel form)
        if keyword:
            prodotti = prodotti.filter(Prodotti.Nome_Prodotto.ilike(f'%{keyword}%') | Prodotti.Descrizione.ilike(f'%{keyword}%'))
        
        if categoria:
            prodotti = prodotti.filter(Prodotti.Categoria == categoria)
        
        if prezzo_min:
            prodotti = prodotti.filter(Prodotti.Prezzo >= prezzo_min)
        
        if prezzo_max:
            prodotti = prodotti.filter(Prodotti.Prezzo <= prezzo_max)
            
        if venditore:
             prodotti = prodotti.filter(Venditori.Nome_Negozio.ilike(f'%{venditore}%'))
        
        return render_template('search_products.html', products=prodotti)

    # Ottengo le categorie distinte dei prodotti
    #SELECT DISTINCT Categoria FROM Prodotti;
    categories = db.session.query(Prodotti.Categoria.distinct())
    return render_template('search_products.html', categories=[c[0] for c in categories])

@app.route('/view_cart')
@buyer_required
def view_cart():
    user_id = session['user_id']
    # Trova il carrello dell'utente
    # SELECT * FROM Carrelli WHERE Acquirente = user_id LIMIT 1;
    carrello = Carrelli.query.filter_by(Acquirente=user_id).first()
    
    if not carrello:
        return render_template('view_cart.html', carrelli=[])

    # Trova gli elementi nel carrello
    # SELECT * FROM Contiene WHERE Carrello = carrello_id;
    items = Contiene.query.filter_by(Carrello=carrello.Id_Carrello).all()
    cart_items = []
    
    for item in items:
        # SELECT * FROM Prodotti WHERE Id_Prodotto = item.Prodotto LIMIT 1;
        prodotto = Prodotti.query.get(item.Prodotto)
        # SELECT * FROM Venditori WHERE Utente = prodotto.Venditore LIMIT 1;
        venditore = Venditori.query.get(prodotto.Venditore)
        cart_items.append({
            'prodotto': prodotto,
            'negozio': venditore.Nome_Negozio,
            'quantità': item.Quantità,
            'totale': prodotto.Prezzo * item.Quantità
        })
    
    return render_template('view_cart.html', carrelli=cart_items)

@app.route('/update_quantity/<int:product_id>', methods=['POST'])
@buyer_required
def update_quantity(product_id):
    new_quantity = request.form.get('quantity', type=int)
    if new_quantity < 1:
        return redirect(url_for('view_cart'))
    
    '''SELECT Contiene.* 
    FROM Contiene
    JOIN Carrelli ON Contiene.Carrello = Carrelli.Id_Carrello
    WHERE Carrelli.Acquirente = user_id
    AND Contiene.Prodotto = product_id
    LIMIT 1;'''
    carrello = db.session.query(Contiene).join(Carrelli).filter(
        Carrelli.Acquirente == session['user_id'],
        Contiene.Prodotto == product_id
    ).first()
    
    carrello.Quantità = new_quantity
    db.session.commit()

    return redirect(url_for('view_cart'))

@app.route('/remove_from_cart/<int:product_id>', methods=['GET', 'POST'])
@buyer_required
def remove_from_cart(product_id):
    '''SELECT Contiene.* 
    FROM Contiene
    JOIN Carrelli ON Contiene.Carrello = Carrelli.Id_Carrello
    WHERE Carrelli.Acquirente = user_id
    AND Contiene.Prodotto = product_id
    LIMIT 1;'''
    carrello = db.session.query(Contiene).join(Carrelli).filter(
        Carrelli.Acquirente == session['user_id'],
        Contiene.Prodotto == product_id
    ).first()

    if carrello:
        db.session.delete(carrello)
        db.session.commit()
    
    return redirect(url_for('view_cart'))

@app.route('/product_details/<int:product_id>', methods=['GET'])
@buyer_required
def product_details(product_id):
    prodotto = Prodotti.query.get_or_404(product_id) 
    venditore = Venditori.query.get_or_404(prodotto.Venditore)
    nome_negozio = venditore.Nome_Negozio
    
    # Valore di default: 'recent'
    order = request.args.get('order', 'recent')  

    '''SELECT Recensioni.*, Utenti.Nome, Utenti.Cognome
    FROM Recensioni
    JOIN Utenti ON Recensioni.Acquirente = Utenti.Id_Utente
    WHERE Recensioni.Prodotto = product_id
    ORDER BY Recensioni.Data/Recensioni.Valutazione order'''
    if order == 'recent':
        recensioni = db.session.query(Recensioni, Utenti.Nome, Utenti.Cognome).join(Utenti, Recensioni.Acquirente == Utenti.Id_Utente).filter(Recensioni.Prodotto == product_id).order_by(Recensioni.Data.desc()).all()
    elif order == 'oldest':
        recensioni = db.session.query(Recensioni, Utenti.Nome, Utenti.Cognome).join(Utenti, Recensioni.Acquirente == Utenti.Id_Utente).filter(Recensioni.Prodotto == product_id).order_by(Recensioni.Data.asc()).all()
    elif order == 'highest_rating':
        recensioni = db.session.query(Recensioni, Utenti.Nome, Utenti.Cognome).join(Utenti, Recensioni.Acquirente == Utenti.Id_Utente).filter(Recensioni.Prodotto == product_id).order_by(Recensioni.Valutazione.desc()).all()
    elif order == 'lowest_rating':
        recensioni = db.session.query(Recensioni, Utenti.Nome, Utenti.Cognome).join(Utenti, Recensioni.Acquirente == Utenti.Id_Utente).filter(Recensioni.Prodotto == product_id).order_by(Recensioni.Valutazione.asc()).all()
    else:
        recensioni = db.session.query(Recensioni, Utenti.Nome, Utenti.Cognome).join(Utenti, Recensioni.Acquirente == Utenti.Id_Utente).filter(Recensioni.Prodotto == product_id).order_by(Recensioni.Data.desc()).all()

    return render_template('product_details.html', prodotto=prodotto, negozio=nome_negozio, recensioni=recensioni)

@app.route('/write_review/<int:product_id>', methods=['GET', 'POST'])
@buyer_required
def write_review(product_id):
    prodotto = Prodotti.query.get_or_404(product_id)
    return render_template('write_review.html', prodotto=prodotto)
    
@app.route('/register_review/<int:product_id>', methods=['POST'])
@buyer_required
def register_review(product_id):
    
    user_id = session.get('user_id')  
    prodotto = product_id
    titolo = request.form['review-title']
    testo = request.form['review-text']
    # Recupera il rating delle stelle
    voto = request.form.get('rating')  

    if not titolo or not testo or not voto:
        prodotto = Prodotti.query.get_or_404(product_id)
        return render_template('write_review.html', prodotto=prodotto)
    
    # Creazione della nuova recensione
    new_review = Recensioni(
        Valutazione = int(voto),  # Assicurati che il voto sia un intero
        Titolo = titolo,
        Testo = testo,
        Data = date.today(),  
        Acquirente = user_id,  
        Prodotto = prodotto  
    )

    # Salvataggio della recensione nel database
    db.session.add(new_review)
    db.session.commit()
    return redirect(url_for('product_details', product_id=product_id))
    
@app.route('/add_to_cart/<int:product_id>', methods=['POST'])
@buyer_required
def add_to_cart(product_id):
    quantity = request.form.get('quantity', type=int)
    if quantity is None or quantity < 1:
        return redirect(url_for('product_details', product_id=product_id))
    
    user_id = session['user_id']
    carrello = Carrelli.query.filter_by(Acquirente=user_id).first()
    
    # Se non esiste il carrello viene creato
    if not carrello:
        carrello = Carrelli(Acquirente=user_id)
        db.session.add(carrello)
        db.session.commit()
    
    # Controlla se il prodotto è già presente nel carrello ed aggiorna i dati di conseguenza
    '''SELECT * 
    FROM Contiene 
    WHERE Carrello = carrello_id 
    AND Prodotto = product_id 
    LIMIT 1;'''
    contiene = Contiene.query.filter_by(Carrello=carrello.Id_Carrello, Prodotto=product_id).first()
    if contiene:
        contiene.Quantità = contiene.Quantità + quantity
    else:
        contiene = Contiene(Carrello=carrello.Id_Carrello, Prodotto=product_id, Quantità=quantity)
        db.session.add(contiene)
    
    db.session.commit()
    return redirect(url_for('view_cart'))
    
@app.route('/purchases')
@buyer_required
def purchases():
    user_id = session['user_id']
    stato_ordine = request.args.get('stato_ordine')
    order_by = request.args.get('order_by', 'id')  # Ordina di default per l'ID

    # Ottengo tutti i prodotti ordinati dall'utente
    '''SELECT Ordini.*, Ordinato.*, Prodotti.*, Venditori.*
    FROM Ordini
    JOIN Ordinato ON Ordini.Id_Ordine = Ordinato.Ordine
    JOIN Prodotti ON Ordinato.Prodotto = Prodotti.Id_Prodotto
    JOIN Venditori ON Prodotti.Venditore = Venditori.Utente
    WHERE Ordini.Acquirente = user_id;'''
    orders_query = (db.session.query(Ordini, Ordinato, Prodotti, Venditori)
                    .join(Ordinato, Ordini.Id_Ordine == Ordinato.Ordine)
                    .join(Prodotti, Ordinato.Prodotto == Prodotti.Id_Prodotto)
                    .join(Venditori, Prodotti.Venditore == Venditori.Utente)
                    .filter(Ordini.Acquirente == user_id))

    # Vengono applicati i filtri in base al tipo di ordini che si vogliono visualizzare
    if stato_ordine:
        orders_query = orders_query.filter(Ordini.Stato_Ordine == stato_ordine)

    # Ordine in base all'impostazione scelta
    if order_by == 'recent':
        orders_query = orders_query.order_by(Ordini.Data_Ordine.desc())
    elif order_by == 'oldest':
        orders_query = orders_query.order_by(Ordini.Data_Ordine.asc())
    else:  # Ordina di default per l'ID
        orders_query = orders_query.order_by(Ordini.Id_Ordine.asc())

    orders = orders_query.all()

    return render_template('purchases.html', orders=orders)


@app.route('/checkout_cart', methods=['GET', 'POST'])
@buyer_required
def checkout_cart():
    user_id = session.get('user_id')
    buyer = Acquirenti.query.filter_by(Id_Utente=user_id).first()
    
    # Recupera il carrello dell'acquirente
    carrello = Carrelli.query.filter_by(Acquirente=buyer.Id_Utente).first()
    
    if not carrello:
        return redirect(url_for('view_cart'))

    # Recupera gli elementi del carrello
    items_in_cart = Contiene.query.filter_by(Carrello=carrello.Id_Carrello).all()
    
    # Crea una lista di articoli per il riepilogo dell'ordine
    cart_items = []
    for item in items_in_cart:
        prodotto = Prodotti.query.get(item.Prodotto)
        negozio = Venditori.query.get(prodotto.Venditore).Nome_Negozio if prodotto.Venditore else 'N/A'
        cart_items.append({
            'prodotto': prodotto,
            'quantità': item.Quantità,
            'totale': prodotto.Prezzo * item.Quantità,
            'negozio': negozio
        })
    
    if request.method == 'POST':
        shipping_address = request.form['address']
        city = request.form['city']
        zip_code = request.form['zip_code']
        payment_method = request.form['payment_method']
        
        # Crea un nuovo ordine
        new_order = Ordini(
            Data_Ordine=date.today(),
            Ora=datetime.now().time(),
            Stato_Ordine="In attesa",
            Indirizzo_Spedizione=f"{shipping_address}, {city}, {zip_code}",
            Metodo_Pagamento=payment_method,
            Acquirente=buyer.Id_Utente
        )
        
        db.session.add(new_order)
        # Flush per ottenere l'Id_Ordine
        db.session.flush()  

        # Aggiunge i prodotti ordinati alla tabella Ordinato
        for item in items_in_cart:
            ordinato_item = Ordinato(
                Ordine=new_order.Id_Ordine,
                Prodotto=item.Prodotto,
                Quantità=item.Quantità
            )
            db.session.add(ordinato_item)
        
        # Rimuovo gli articoli dal carrello
        Contiene.query.filter_by(Carrello=carrello.Id_Carrello).delete()

        # Elimino il carrello dopo il checkout
        db.session.delete(carrello)
        
        db.session.commit()
        
        return redirect(url_for('purchases'))

    # Recupera l'indirizzo di default dell'utente
    default_address = buyer.utente.Indirizzo

    return render_template('checkout_cart.html', default_address=default_address, cart_items=cart_items)
                         
@app.route('/checkout_product_get/<int:product_id>', methods=['GET', 'POST']) 
@buyer_required
def checkout_product_get(product_id):
    user_id = session.get('user_id')
    buyer = Acquirenti.query.filter_by(Id_Utente=user_id).first()
    
    product = Prodotti.query.get(product_id)  # Ottengo il prodotto dal database
    
    # Mostra l'indirizzo di default dell'utente
    default_address = buyer.utente.Indirizzo

    if request.method == 'POST':
        quantity = request.form.get('quantity', default=1, type=int)
    else:
        quantity = 1

    total = quantity * product.Prezzo

    seller = product.venditore.Nome_Negozio

    return render_template('checkout_product.html', default_address=default_address, product=product, quantity=quantity, total=total, seller=seller)

@app.route('/checkout_product_post/<int:product_id>', methods=['GET', 'POST']) 
@buyer_required
def checkout_product_post(product_id):
    user_id = session.get('user_id')
    buyer = Acquirenti.query.filter_by(Id_Utente=user_id).first()
    
    if request.method == 'POST':
        shipping_address = request.form['address']
        city = request.form['city']
        zip_code = request.form['zip_code']
        payment_method = request.form['payment_method']
        
        # Crea un nuovo ordine
        new_order = Ordini(
            Data_Ordine=date.today(),
            Ora=datetime.now().time(),
            Stato_Ordine="In attesa",
            Indirizzo_Spedizione=f"{shipping_address}, {city}, {zip_code}",
            Metodo_Pagamento=payment_method,
            Acquirente=buyer.Id_Utente
        )
        
        db.session.add(new_order)
        db.session.flush()  # Flush per ottenere l'Id_Ordine

        quantity = request.form.get('quantity', 1)  # Di default 1 se non viene passata nessuna quantità
        # Aggiungo il prodotto all'ordine
        ordinato_item = Ordinato(
            Ordine=new_order.Id_Ordine,
            Prodotto=product_id,
            Quantità=quantity
        )

        db.session.add(ordinato_item)
        db.session.commit()
        
        return redirect(url_for('purchases'))

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)


    
