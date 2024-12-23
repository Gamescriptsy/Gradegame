from app import db
from models import Game

# Buat tabel
db.create_all()

# Tambah data awal untuk game
games = [
    Game(name="Free Fire", image="freefire.jpg"),
    Game(name="Mobile Legends", image="mobilelegends.jpg"),
    Game(name="PUBG Mobile", image="pubgmobile.jpg")
]

db.session.add_all(games)
db.session.commit()
print("Database dan data awal berhasil dibuat!")
