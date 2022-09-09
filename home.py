from unicodedata import name
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash, check_password_hash
import yaml

app = Flask(__name__)
app.secret_key = b'42'

db = yaml.full_load(open("db.yaml"))
app.config["MYSQL_HOST"] = db["mysql_host"]
app.config["MYSQL_USER"] = db["mysql_user"]
app.config["MYSQL_PASSWORD"] = db["mysql_password"]
app.config["MYSQL_DB"] = db["mysql_db"]

mysql = MySQL(app)

@app.route("/", methods=["GET", "POST"])
def indexHome():
    error = None
    cpfValidador = None
    cpfLogin = None
    if request.method == "POST":
        userDetails = request.form
        cpfLogin = userDetails["cpfLogin"]
        senhaLogin = userDetails["senhaLogin"]
        cur = mysql.connection.cursor()
        cur.execute("SELECT senha FROM users WHERE cpf = %s", [cpfLogin])
        senhaCriptografada = cur.fetchone()
        cur.execute("SELECT cpf FROM users WHERE cpf = %s", [cpfLogin])
        cpfValidador = cur.fetchone()
        if not cpfValidador and not senhaCriptografada:
            flash("Preencha todos os campos!")
            cpfValidador = [1]
            senhaCriptografada = [1]
        #mysql.connection.commit()
        #cur.close()
        if cpfValidador[0] != cpfLogin:
            flash("CPF não existe no sistema!")
            return redirect ("/")
        else:
            if check_password_hash(senhaCriptografada[0], senhaLogin):
                return redirect ("/home")
            else:
                flash("Senha incorreta!")
                return redirect ("/")
    return render_template("login.html", error = error)

@app.route("/cadastro", methods=["GET", "POST"])
def indexCadastro():    
    #configurando a aquisicão das variaveis do formulario em HTML pelo request em Python
    if request.method == "POST":
        userDetails = request.form
        name = userDetails["nome"]
        cpf = userDetails["cpf"]
        senha = userDetails["senha"]
        senhaCriptografada = generate_password_hash(senha)
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO users(nome, cpf, senha) VALUES(%s, %s, %s)", (name, cpf, senhaCriptografada))
        mysql.connection.commit()
        cur.close()
        return redirect (url_for('indexLogin'))
    return render_template("cadastro.html")

@app.route("/home", methods=["GET", "POST"])
def home():
    
    return render_template("home.html")
app.run(debug=True) #comando inicia automaticamente o programa, habilitando o debug sempre que algo for atualizado!