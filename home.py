from xml.dom import UserDataHandler
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash, check_password_hash
import yaml
import random as r

#Aqui inicializo o framework Flask e todas as suas funções pela varíavel "app".
app = Flask(__name__)
#Chave secreta para funcionamento do framework Flash, sem ele não funciona! 42 foi um número que escolhi como senha.
app.secret_key = b'42'

#Aqui chamo e digo para que o framework Yaml seja completamente carregado através de uma variável chamada "db". Solicito para que abra as configurações localizadas no arquivo "db.yaml". Lá estão carregadas as diretrizes para que o Workbench do MySQL funcione. 
#Abra e edite o arquivo "db.yaml", se precisar. O nome do user, como padrão, está root. Edite tbm a senha, mudando para aquela que você configurou no seu computador! Dica: geralmente a senha dos computadores da fatec é "fatec".
db = yaml.full_load(open("db.yaml"))
app.config["MYSQL_HOST"] = db["mysql_host"]
app.config["MYSQL_USER"] = db["mysql_user"]
app.config["MYSQL_PASSWORD"] = db["mysql_password"]
app.config["MYSQL_DB"] = db["mysql_db"]

#Aqui inicializo o framework MySQL do flask_mysqldb e todas as suas funções pela varíavel "mysql".
mysql = MySQL(app)

#Rota de página web criada. Ela está localizada em localhost/ . Página principal, página de Login com link para redirecionar à página Cadastro. 
#Utiliza os métodos GET para pegar informações do banco de dados. POST para mandar informações pro banco de dados.
@app.route("/", methods=["GET", "POST"])
def indexHome():
    error = None
    cpfValidador = None
    cpfLogin = None
    nomeUsuario = None
    contaUsuario = None
    agenciaUsuario = None
    saldoUsuario = None

    if request.method == "POST":
        userDetails = request.form
        cpfLogin = userDetails["cpfLogin"]
        senhaLogin = userDetails["senhaLogin"]
        cur = mysql.connection.cursor()

        cur.execute("SELECT senha FROM users WHERE cpf = %s", [cpfLogin])
        senhaCriptografada = cur.fetchone()

        cur.execute("SELECT cpf FROM users WHERE cpf = %s", [cpfLogin])
        cpfValidador = cur.fetchone()

        cur.execute("SELECT nome FROM users WHERE cpf = %s", [cpfLogin])
        nomeUsuario = cur.fetchone()
        session['nomeUsuario'] = nomeUsuario[0]

        cur.execute("SELECT numeroAgencia FROM users WHERE cpf = %s", [cpfLogin])
        agenciaUsuario = cur.fetchone()
        session['agenciaUsuario'] = agenciaUsuario[0]

        cur.execute("SELECT contaBancaria FROM users WHERE cpf = %s", [cpfLogin])
        contaUsuario = cur.fetchone()
        session['contaUsuario'] = contaUsuario[0]

        cur.execute("SELECT saldoBancario FROM users WHERE cpf = %s", [cpfLogin])
        saldoUsuario = cur.fetchone()
        session['saldoUsuario'] = saldoUsuario[0]

        if not cpfValidador and not senhaCriptografada:
            flash("Preencha todos os campos!")
            cpfValidador = [1]
            senhaCriptografada = [1]
            return redirect ("/")

        #Existe um bug aqui, ele não separa preencha o campo com cpf não existe no sistema.
        if cpfValidador[0] != cpfLogin:
            flash("CPF não existe no sistema!")
            return redirect ("/")
        else:
            if check_password_hash(senhaCriptografada[0], senhaLogin):
                return redirect (url_for('home'))
            else:
                flash("Senha incorreta!")
                return redirect ("/")
        
    return render_template("login.html", error = error)



@app.route("/cadastro", methods=["GET", "POST"])
def indexCadastro():
    numeroAgencia = "000"
    contaBancaria = None
    saldoBancario = None
    #configurando a aquisicão das variaveis do formulario em HTML pelo request em Python
    if request.method == "POST":

        userDetails = request.form
        name = userDetails["nome"]
        cpf = userDetails["cpf"]
        senha = userDetails["senha"]
        senhaCriptografada = generate_password_hash(senha)

        #Criando conta bancaria aleatoria de 9 digitos
        numero = []
        for i in range(1, 10):
            numero.append(r.randint(0, 9))
        contaBancaria="".join(map(str,numero))

        #Criando numero de agencia de 4 digitos
        if contaBancaria is not None:
            numeroAgencia = numeroAgencia + "1"
            saldoBancario = 0

        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO users(nome, cpf, senha, contaBancaria, numeroAgencia, saldoBancario) VALUES(%s, %s, %s, %s, %s, %s)", (name, cpf, senhaCriptografada, contaBancaria, numeroAgencia, saldoBancario))
        mysql.connection.commit()
        cur.close()
        return redirect (url_for('indexHome'))
    
    return render_template("cadastro.html")



@app.route("/home", methods=["GET", "POST"])
def home():
    testeConta = None
    testeAgencia = None
    testeCpf = None
    saldoParcial = None
    saldoFinal = None
    if request.method == "POST":

        userDetails = request.form
        numConta = userDetails["numConta"]
        numAgencia = userDetails["numAgencia"]
        numCpf = userDetails["numCpf"]
        valorDeposito = userDetails["valorDeposito"]

        cur = mysql.connection.cursor()
        cur.execute("SELECT contaBancaria FROM users WHERE contaBancaria = %s", [numConta])
        testeConta = cur.fetchone()
        cur.execute("SELECT numeroAgencia FROM users WHERE contaBancaria = %s", [numConta])
        testeAgencia = cur.fetchone()
        cur.execute("SELECT cpf FROM users WHERE contaBancaria = %s", [numConta])
        testeCpf = cur.fetchone()
        cur.execute("SELECT saldoBancario FROM users WHERE contaBancaria = %s", [numConta])
        saldoParcial = cur.fetchone()

        if testeConta[0] == numConta and testeAgencia[0] == numAgencia and testeCpf[0] == numCpf:
            saldoFinal = saldoParcial[0]
            saldoFinal = int(saldoFinal) + int(valorDeposito)
            cur.execute("UPDATE users SET saldoBancario = %s", [saldoFinal])
            mysql.connection.commit()
            cur.close()

        session.pop('saldoUsuario', None)
        session['saldoUsuario'] = saldoFinal
        return redirect (url_for('home'))

    return render_template("menu-lateral.html")
    


app.run(debug=True) #comando inicia automaticamente o programa, habilitando o debug sempre que algo for atualizado!