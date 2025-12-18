from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from sqlalchemy import MetaData
from sqlalchemy_serializer import SerializerMixin

# ---- App & DB setup ----

metadata = MetaData(naming_convention={
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
})

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///app.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(metadata=metadata, model_class=SerializerMixin)
db.init_app(app)
migrate = Migrate(app, db)

# ---- Models ----

class User(db.Model, SerializerMixin):
    __tablename__ = "users"

    # Include posts, but stop recursion at posts.user
    serialize_rules = ("-posts.user",)

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)

    # backref gives User.posts automatically
    posts = db.relationship("Post", backref="user", lazy=True)

    def __repr__(self):
        return f"<User {self.name}>"


class Post(db.Model, SerializerMixin):
    __tablename__ = "posts"

    # If you serialize posts directly, avoid going back into user.posts
    serialize_rules = ("-user.posts",)

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    def __repr__(self):
        return f"<Post {self.title}>"

# ---- Routes ----

@app.route("/users", methods=["GET"])
def get_users():
    users = User.query.all()
    # Each user includes their posts because of the relationship + serialize_rules
    return jsonify([u.to_dict() for u in users])

@app.route("/users", methods=["POST"])
def create_user():
    data = request.get_json() or {}
    name = data.get("name")

    if not name:
        return jsonify({"error": "name is required"}), 400

    user = User(name=name)
    db.session.add(user)
    db.session.commit()

    return jsonify(user.to_dict()), 201

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
