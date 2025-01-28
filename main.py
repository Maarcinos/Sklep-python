import os
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'klucz'


UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///mydatabase.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

db = SQLAlchemy(app)


class Ogloszenie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nazwa = db.Column(db.String(80), nullable=False)
    opis = db.Column(db.String(200), nullable=False)
    cena = db.Column(db.Integer, nullable=False)
    zdjecie = db.Column(db.String(120))


with app.app_context():
    db.create_all()


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/', methods=["POST", "GET"])
def formularz():
    if request.method == "POST":
        nazwa = request.form['nazwa']
        opis = request.form['opis']
        cena = request.form['cena']
        zdjecie = request.files.get('zdjecie')

        if not nazwa or not opis or not cena:
            flash("Wszystkie pola muszą być wypełnione", "error")
        else:
            filename = None
            if zdjecie and allowed_file(zdjecie.filename):
                filename = secure_filename(zdjecie.filename)
                zdjecie_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                zdjecie.save(zdjecie_path)

            nowe_ogloszenie = Ogloszenie(nazwa=nazwa, opis=opis, cena=cena, zdjecie=filename)
            db.session.add(nowe_ogloszenie)
            db.session.commit()
            flash("Ogłoszenie dodane pomyślnie!", "success")
            return redirect(url_for('formularz'))

    wszystkie_ogloszenia = Ogloszenie.query.all()
    return render_template("index.html", ogloszenia=wszystkie_ogloszenia)

@app.route('/delete/<int:id>', methods=["POST"])
def delete_ogloszenie(id):
    ogloszenie = Ogloszenie.query.get_or_404(id)
    db.session.delete(ogloszenie)
    db.session.commit()
    return redirect(url_for('formularz'))

@app.route('/ogloszenie/<int:id>', methods=["GET"])
def ogloszenie_details(id):
    ogloszenie = Ogloszenie.query.get_or_404(id)
    return render_template("ogloszenie_datails.html", ogloszenie=ogloszenie)


@app.route('/add_to_cart/<int:id>')
def add_to_cart(id):
    ogloszenie = Ogloszenie.query.get_or_404(id)
    if 'cart' not in session:
        session['cart'] = []
    session['cart'].append(ogloszenie.id)
    session.modified = True
    flash('Dodano do koszyka!', 'success')
    return redirect(url_for('formularz'))

# Wyświetlanie koszyka
@app.route('/koszyk')

def koszyk():
    cart_items = Ogloszenie.query.filter(Ogloszenie.id.in_(session.get('cart', []))).all()
    total_price = sum(item.cena for item in cart_items)
    return render_template('koszyk.html', ogloszenia=cart_items, total_price=total_price)


@app.route('/remove_from_cart/<int:id>')
def remove_from_cart(id):
    if 'cart' in session and id in session['cart']:
        session['cart'].remove(id)
        session.modified = True
        flash('Usunięto z koszyka!', 'success')
    return redirect(url_for('koszyk'))

if __name__ == '__main__':
    app.run(debug=True)
