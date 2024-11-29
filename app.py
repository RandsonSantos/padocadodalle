from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
import json
from datetime import timedelta

app = Flask(__name__)
app.secret_key = 'sua_chave_secreta_aqui'  # Altere para uma chave secreta segura

# Configuração do banco de dados SQLite
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///padaria.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Modelo do Produto
class Produto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    valor = db.Column(db.String(20), nullable=False)
    categoria_id = db.Column(db.Integer, db.ForeignKey('categoria.id'), nullable=False)

# Modelo da Categoria
class Categoria(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(50), nullable=False)
    produtos = db.relationship('Produto', backref='categoria', lazy=True)

# Criação do banco de dados
with app.app_context():
    db.create_all()

def load_users():
    with open('json/user.json') as f:
        return json.load(f)['users']
    

def check_credentials(username, password):
    users = load_users()
    for user in users:
        if user["username"] == username and user["password"] == password:
            return True
    return False

@app.route('/')
def menu():
    produtos = Produto.query.all()
    categorias = Categoria.query.all()
    cardapio = {}
    for categoria in categorias:
        cardapio[categoria.nome] = Produto.query.filter_by(categoria_id=categoria.id).all()
    return render_template('menu.html', cardapio=cardapio)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if check_credentials(username, password):
            session['user'] = username
            session.permanent = True  # Sessão permanente com tempo limite
            return redirect(url_for('admin'))
        else:
            return 'Nome de usuário ou senha incorretos!'
    return render_template('login.html', title="Área Administrativa")

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if 'user' not in session:
        return redirect(url_for('login'))
    
    produtos = Produto.query.all()
    categorias = Categoria.query.all()
    categoria_filtro = request.form.get('categoria_filtro')
    if categoria_filtro:
        produtos = Produto.query.join(Categoria).filter(Categoria.nome == categoria_filtro).all()
    return render_template('admin.html', produtos=produtos, categorias=categorias)

@app.route('/add_produtos', methods=['POST'])
def add_produtos():
    if 'user' not in session:
        return redirect(url_for('login'))
    
    nome = request.form.get('nome')
    valor = request.form.get('valor')
    categoria_id = request.form.get('categoria_id')
    if nome and valor and categoria_id:
        novo_produto = Produto(nome=nome, valor=valor, categoria_id=categoria_id)
        db.session.add(novo_produto)
        db.session.commit()
    return redirect(url_for('admin'))

@app.route('/add_categoria', methods=['POST'])
def add_categoria():
    if 'user' not in session:
        return redirect(url_for('login'))
    
    nova_categoria = request.form.get('nova_categoria')
    if nova_categoria:
        categoria_existente = Categoria.query.filter_by(nome=nova_categoria).first()
        if not categoria_existente:
            nova_categoria = Categoria(nome=nova_categoria)
            db.session.add(nova_categoria)
            db.session.commit()
    return redirect(url_for('admin'))

@app.route('/editar_produtos/<int:id>', methods=['GET', 'POST'])
def edit_produtos(id):
    if 'user' not in session:
        return redirect(url_for('login'))
    
    produto = Produto.query.get_or_404(id)
    categorias = Categoria.query.all()
    if request.method == 'POST':
        produto.nome = request.form.get('nome')
        produto.valor = request.form.get('valor')
        produto.categoria_id = request.form.get('categoria_id')
        db.session.commit()
        return redirect(url_for('admin'))
    return render_template('editar_produtos.html', produto=produto, categorias=categorias)

@app.route('/delete_produto/<int:id>', methods=['POST'])
def delete_produto(id):
    if 'user' not in session:
        return redirect(url_for('login'))

    produto = Produto.query.get_or_404(id)
    db.session.delete(produto)
    db.session.commit()
    return redirect(url_for('admin'))

@app.route('/lista_produtos')
def lista_produtos():
    produtos = Produto.query.all()
    return render_template('lista_produtos.html', produtos=produtos)

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=1)

if __name__ == '__main__':
    app.run(debug=True)
