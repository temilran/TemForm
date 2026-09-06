import smtplib
import email
import random
import os
from email.policy import default
import jwt
from datetime import datetime, timedelta, timezone

from dotenv import load_dotenv

load_dotenv()

from flask import Flask, render_template, url_for, request, redirect, flash, make_response, session
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:29052007@localhost/users'
app.config['SECRET_KEY'] = os.getenv("SECRET_KEY", "dfgyuhnjimkoasfsdfs")
db = SQLAlchemy(app)


class article(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    intro = db.Column(db.String(100), nullable=False)
    title = db.Column(db.String(300), nullable=False)
    text = db.Column(db.Text, nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, nullable=False)
    us_likes = db.relationship('likes', backref='article', cascade='all, delete-orphan', lazy=True)
    comments = db.relationship('comments', backref='parent_article', cascade='all, delete-orphan', lazy=True)

    def __repr__(self):
        return 'article %r' % self.id


class likes(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    article_id = db.Column(db.Integer, db.ForeignKey('article.id', ondelete="CASCADE"), nullable=False)
    user_id = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return 'likes %r' % self.id


class comments(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    article_id = db.Column(db.Integer, db.ForeignKey('article.id', ondelete="CASCADE"), nullable=False)
    user_id = db.Column(db.Integer, nullable=False)
    likes = db.relationship('comment_likes', backref='comment', cascade='all, delete-orphan', lazy=True)

    def __repr__(self):
        return 'comments %r' % self.id


class comment_likes(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    comment_id = db.Column(db.Integer, db.ForeignKey('comments.id', ondelete="CASCADE"), nullable=False)
    user_id = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return 'comment_likes %r' % self.id


def get_current_viewer():
    token = request.cookies.get('auth_token')
    if not token:
        return None

    try:
        data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        return data
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None


@app.route('/')
@app.route('/posts')
def posts():
    current_viewer = get_current_viewer()
    articles = article.query.order_by(article.date.desc()).all()
    return render_template("posts.html", articles=articles, current_viewer=current_viewer)


@app.route('/about')
def about():
    current_viewer = get_current_viewer()
    return render_template("about.html", current_viewer=current_viewer)


@app.route('/account')
def account():
    current_viewer = get_current_viewer()
    if not current_viewer:
        return redirect('/avtor')

    return render_template("account.html", user_data=current_viewer, current_viewer=current_viewer)


@app.route('/logout')
def logout():
    response = make_response(redirect('/avtor'))
    response.set_cookie('auth_token', '', expires=0)
    flash("Вы вышли с аккаунта!")
    return response


@app.route("/create-article", methods=["POST", "GET"])
def create_article():
    current_viewer = get_current_viewer()
    if not current_viewer:
        return redirect('/avtor')

    user_id = current_viewer['user_id']

    if request.method == "POST":
        title = request.form['title']
        intro = request.form['intro']
        text = request.form['text']

        Article = article(title=title, intro=intro, text=text, user_id=user_id)

        try:
            db.session.add(Article)
            db.session.commit()
            return redirect('/posts')
        except:
            db.session.rollback()
            return "При добавлении статьи произошла ошибка"

    else:
        return render_template("create-article.html", current_viewer=current_viewer)


@app.route('/posts_detaile/<int:id>')
def posts_detaile(id):
    current_viewer = get_current_viewer()

    Article = article.query.get(id)
    if not Article:
        flash("Ошибка 404. Статья не найдена")
        return redirect('/')

    likes_count = db.session.query(likes).filter(likes.article_id == id).count()
    coments = comments.query.filter_by(article_id=id).order_by(comments.date.desc()).all()

    return render_template(
        "posts_detaile.html",
        article=Article,
        likes_count=likes_count,
        comments=coments,
        current_viewer=current_viewer
    )


@app.route("/post_update/<int:id>", methods=["POST", "GET"])
def update_article(id):
    current_viewer = get_current_viewer()
    if not current_viewer:
        return redirect('/avtor')

    Article = article.query.get(id)

    if not Article:
        return "Статья не найдена", 404

    if request.method == "POST":
        Article.title = request.form['title']
        Article.intro = request.form['intro']
        Article.text = request.form['text']

        try:
            db.session.commit()
            flash("Пост успешно обновлен!")
            return redirect('/posts')
        except:
            flash("При редактировании статьи произошла ошибка")
            return redirect(f'/post_update/{id}')

    else:
        return render_template("post_update.html", article=Article, current_viewer=current_viewer)


@app.route("/posts/<int:id>/del")
def posts_delete(id):
    current_viewer = get_current_viewer()
    if not current_viewer:
        return redirect('/avtor')

    Article = article.query.get_or_404(id)

    if current_viewer['user_id'] == Article.user_id or current_viewer.get('role') in ['owner', 'admin']:
        try:
            db.session.delete(Article)
            db.session.commit()
            flash("Пост успешно удален!")
            return redirect('/posts')
        except:
            return "При удалении статьи произошла ошибка"
    else:
        flash("У вас нет прав на удаление этого поста!")
        return redirect('/posts')


@app.route("/posts/<int:id>/likes")
def posts_likes(id):
    current_viewer = get_current_viewer()
    current_article_likes = likes.query.filter_by(article_id=id).order_by(likes.date.desc()).all()
    Article = article.query.get(id)
    return render_template("posts_likes.html", article_likes=current_article_likes, article=Article,
                           current_viewer=current_viewer)


@app.route('/like/<int:article_id>', methods=['POST'])
def add_like(article_id):
    current_viewer = get_current_viewer()
    if not current_viewer:
        return redirect('/avtor')
    user_id = current_viewer['user_id']

    existing_like = likes.query.filter_by(user_id=user_id, article_id=article_id).first()
    if not existing_like:
        new_like = likes(user_id=user_id, article_id=article_id)
        db.session.add(new_like)
    else:
        db.session.delete(existing_like)

    db.session.commit()
    return redirect(f'/posts_detaile/{article_id}')


@app.route('/comment/<int:article_id>', methods=['POST'])
def add_comments(article_id):
    current_viewer = get_current_viewer()
    if not current_viewer:
        return redirect('/avtor')

    comment = request.form.get('text')
    user_id = current_viewer['user_id']
    if comment and comment.strip():
        new_comment = comments(text=comment, user_id=user_id, article_id=article_id)
        try:
            db.session.add(new_comment)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            return f"Ошибка базы: {e}"

    return redirect(f'/posts_detaile/{article_id}')


@app.route('/comm_like/<int:article_id>/<int:comment_id>', methods=['POST'])
def add_commlike(article_id, comment_id):
    current_viewer = get_current_viewer()
    if not current_viewer:
        return redirect('/avtor')

    user_id = current_viewer['user_id']
    existing_like = comment_likes.query.filter_by(user_id=user_id, comment_id=comment_id).first()
    if not existing_like:
        new_like = comment_likes(user_id=user_id, comment_id=comment_id)
        db.session.add(new_like)
    else:
        db.session.delete(existing_like)

    db.session.commit()
    return redirect(f'/posts_detaile/{article_id}')


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5000)