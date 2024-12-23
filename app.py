from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import login_user, login_required, logout_user, current_user
from extensions import db, login_manager
from models_manager import Manager
from flask_socketio import SocketIO, emit
from flask_migrate import Migrate

# Inisialisasi aplikasi
app = Flask(__name__)
app.secret_key = "supersecretkey"

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///default.db'  # Default database (wajib)
app.config['SQLALCHEMY_BINDS'] = {
    'user_db': 'sqlite:///database.db',
    'manager_db': 'sqlite:///manager.db',
}
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Hubungkan database dan login manager ke aplikasi
migrate = Migrate(app, db)
db.init_app(app)
login_manager.init_app(app)
login_manager.login_view = "login"

with app.app_context():
    from models import User, Game, Transaction
    from models_manager import Manager
    
    # Buat semua tabel berdasarkan BINDS
    db.create_all()  # SQLAlchemy akan membuat tabel berdasarkan SQLALCHEMY_BINDS

@login_manager.user_loader
def load_user(user_id):
    # Coba cari user di database user
    user = User.query.get(int(user_id))
    if user:
        return user
    
    # Jika tidak ditemukan di user, coba cari di manager
    manager = Manager.query.get(int(user_id))
    if manager:
        return manager
    
    return None


# Tambahkan route Anda di sini
@app.route("/")
def index():
    games = Game.query.all()
    return render_template("index.html", games=games)

@app.route("/manager/dashboard")
@login_required
def manager_dashboard():
    users_count = User.query.count()
    transactions_count = Transaction.query.count()
    games_count = Game.query.count()
    total_income = db.session.query(db.func.sum(Transaction.amount)).scalar() or 0
    return render_template("manager_dashboard.html", 
                           manager=current_user,
                           users_count=users_count, 
                           transactions_count=transactions_count,
                           games_count=games_count,
                           total_income=total_income)


# Lihat Semua Transaksi
@app.route("/manager/transactions")
@login_required
def manager_transactions():
    transactions = Transaction.query.all()
    return render_template("manager_transactions.html", transactions=transactions)

# Konfirmasi atau Batalkan Transaksi
@app.route("/manager/transactions/update", methods=["POST"])
@login_required
def update_transaction():
    transaction_id = request.form.get("transaction_id")
    status = request.form.get("status")  # 'confirmed' or 'canceled'

    transaction = Transaction.query.get(transaction_id)
    if transaction:
        transaction.status = status
        db.session.commit()
        flash("Status transaksi diperbarui!", "success")
    else:
        flash("Transaksi tidak ditemukan!", "danger")
    return redirect(url_for("manager_transactions"))

# CRUD Data Game
@app.route("/manager/games")
@login_required
def manage_games():
    games = Game.query.all()
    return render_template("manager_games.html", games=games)

@app.route("/manager/games/add", methods=["POST"])
@login_required
def add_game():
    name = request.form.get("name")
    image = request.form.get("image")
    new_game = Game(name=name, image=image)
    db.session.add(new_game)
    db.session.commit()
    flash("Game berhasil ditambahkan!", "success")
    return redirect(url_for("manage_games"))

@app.route("/manager/games/delete/<int:game_id>")
@login_required
def delete_game(game_id):
    game = Game.query.get(game_id)
    if game:
        db.session.delete(game)
        db.session.commit()
        flash("Game berhasil dihapus!", "success")
    else:
        flash("Game tidak ditemukan!", "danger")
    return redirect(url_for("manage_games"))

@app.route("/manager/users")
@login_required
def manage_users():
    # Ambil semua pengguna dari database
    users = User.query.all()
    return render_template("manager_users.html", users=users)


@app.route("/manager/users/ban/<int:user_id>")
@login_required
def ban_user(user_id):
    user = User.query.get(user_id)
    if user:
        # Cek apakah ada transaksi aktif
        active_transactions = Transaction.query.filter_by(user_id=user.id).first()
        if active_transactions:
            flash("User memiliki transaksi aktif tetapi akan ditandai sebagai diblokir.", "warning")
        
        # Tandai user sebagai diblokir
        user.is_banned = True
        db.session.commit()
        flash("User berhasil diblokir!", "success")
    else:
        flash("User tidak ditemukan!", "danger")
    return redirect(url_for("manage_users"))




@app.route("/manager/reports")
@login_required
def transaction_reports():
    total_income = db.session.query(db.func.sum(Transaction.amount)).scalar() or 0
    return render_template("view_reports.html", total_income=total_income)

@app.route("/register_manager", methods=["GET", "POST"])
def register_manager():
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]

        if Manager.query.filter((Manager.username == username) | (Manager.email == email)).first():
            flash("Username atau email sudah terdaftar", "danger")
            return redirect(url_for("register_manager"))

        new_manager = Manager(username=username, email=email)
        new_manager.set_password(password)
        db.session.add(new_manager)
        db.session.commit()
        flash("Registrasi Manager berhasil!", "success")
        return redirect(url_for("login"))
    return render_template("register_manager.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        role = request.form.get("role", "user")  # Default to user

        if role == "user":
            # Check user credentials
            user = User.query.filter_by(username=username).first()
            if user and user.check_password(password):
                login_user(user)
                flash("Login berhasil!", "success")
                return redirect(url_for("index"))
        elif role == "manager":
            # Check manager credentials
            manager = Manager.query.filter_by(username=username).first()
            if manager and manager.check_password(password):
                login_user(manager)
                flash("Login berhasil sebagai Manager!", "success")
                return redirect(url_for("manager_dashboard"))

        flash("Username atau password salah", "danger")
    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]

        # Validasi username dan email
        if User.query.filter((User.username == username) | (User.email == email)).first():
            flash("Username atau email sudah terdaftar", "danger")
            return redirect(url_for("register"))

        new_user = User(username=username, email=email)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        flash("Registrasi berhasil! Silakan login.", "success")
        return redirect(url_for("login"))
    return render_template("register.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Anda telah logout", "info")
    return redirect(url_for("index"))

@app.route("/profile")
@login_required
def profile():
    last_transaction = Transaction.query.filter_by(user_id=current_user.id).order_by(Transaction.created_at.desc()).first()
    return render_template("profile.html", user=current_user, last_transaction=last_transaction)


@app.route("/topup/<game_name>", methods=["GET", "POST"])
@login_required
def topup(game_name):
    if current_user.is_banned:
        flash("Akun Anda telah diblokir dan tidak dapat melakukan transaksi.", "danger")
        return redirect(url_for("profile"))

    templates = {
        "freefire": "topup_freefire.html",
        "mobilelegends": "topup_mlbb.html",
        "pubgmobile": "topup_pubg.html"
    }

    game_ids = {
        "freefire": 1,
        "mobilelegends": 2,
        "pubgmobile": 3
    }

    if game_name not in templates:
        abort(404)

    if request.method == "POST":
        user_game_id = request.form['user_id']  # ID game user
        nominal_and_price = request.form['nominal'].split('|')
        nominal = nominal_and_price[0]  
        price = int(nominal_and_price[1])
        payment_method = request.form['payment_method']
        
        # Buat transaksi baru
        transaction = Transaction(
            user_id=current_user.id,  # ID user yang login
            game_id=game_ids[game_name],  # ID game dari mapping
            user_game_id=user_game_id,  # ID game user
            item_name=nominal,
            amount=price,
            payment_method=payment_method,
            status='pending'
        )
        
        try:
            db.session.add(transaction)
            db.session.commit()
            flash("Top up berhasil!", "success")
            return redirect(url_for("transaksi_berhasil", 
                                  game_name=game_name, 
                                  user_game_id=user_game_id,
                                  nominal=nominal,
                                  payment_method=payment_method))
        except Exception as e:
            db.session.rollback()
            flash("Terjadi kesalahan saat memproses transaksi.", "danger")
            return redirect(url_for("topup", game_name=game_name))

    # GET request
    game = Game.query.get(game_ids[game_name])
    return render_template(templates[game_name], game=game)

@app.route("/transaksi-berhasil")
@login_required
def transaksi_berhasil():
    # Mendapatkan parameter dari URL
    game_name = request.args.get("game_name")
    user_game_id = request.args.get("user_game_id")
    nominal = request.args.get("nominal")
    payment_method = request.args.get("payment_method")

    # Menyediakan informasi transaksi untuk ditampilkan di halaman transaksi berhasil
    return render_template("transaksi_berhasil.html", 
                           game_name=game_name, 
                           user_game_id=user_game_id, 
                           nominal=nominal, 
                           payment_method=payment_method)


@app.route("/transactions")
@login_required
def transaction_history():
    # Ambil semua transaksi beserta data game
    transactions = Transaction.query.join(Game, Transaction.game_id == Game.id).add_columns(
        Transaction.id, Transaction.user_game_id, Transaction.item_name, 
        Transaction.amount, Transaction.payment_method, Transaction.status, 
        Game.name.label("game_name")
    ).all()
    return render_template("transactions.html", transactions=transactions)


if __name__ == "__main__":
    app.run(debug=True) 
