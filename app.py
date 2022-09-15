from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash, check_password_hash
import yaml
import random

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

    #Inicializando as variaveis. None = Vazias, até que elas recebam outro valor.
    error = None

    #Inicialização dos componentes de indexHome, caso o método utilizado seja POST. Ou seja, se o usuário clicar em enviar informações ao Servidor.
    if request.method == "POST":

        #userDetails é uma variável que carregará o request.form do Flask: request.
        userDetails = request.form

        #Todas as vezes que userDetails receber entre caixas uma variável, como abaixo, ele está recebendo informações das quais o usuário digitou em algum formulario do Template HTML que está retornando no final do def indexHome.
        cpfLogin = userDetails["cpfLogin"]
        senhaLogin = userDetails["senhaLogin"]

        #Inicilizando o MySQL, através da variável cur.
        cur = mysql.connection.cursor()

        #Pedindo ao SQL que execute a linha de código a seguir. Selecionar uma das colunas da tabela users onde o cpf seja um valor igual a "%s", e por "%s" ele entende que seja o que estiver na variável cpfLogin.
        cur.execute("SELECT senha FROM users WHERE cpf = %s", [cpfLogin])
        #O resultado da query acima será "capturado" através de fetchone() dentro da variável senhaCriptografada. Parece que ao ser capturado o resultado vira uma lista. VERIFICAR ISSO.
        senhaCriptografada = cur.fetchone()

        #Consertar bug de verificação de CPF no login.
        cur.execute("SELECT cpf FROM users WHERE cpf = %s", [cpfLogin])
        cpfValidador = cur.fetchone()

        cur.execute("SELECT nome FROM users WHERE cpf = %s", [cpfLogin])
        nomeUsuario = cur.fetchone()
        #Primeira aparição de session, um framework de Flask. Ele pega uma variável e permite que ela seja utilizada globalmente.
        session['nomeUsuario'] = nomeUsuario[0]

        cur.execute("SELECT agenciaBancaria FROM users WHERE cpf = %s", [cpfLogin])
        agenciaUsuario = cur.fetchone()
        session['agenciaUsuario'] = agenciaUsuario[0]

        cur.execute("SELECT contaBancaria FROM users WHERE cpf = %s", [cpfLogin])
        contaUsuario = cur.fetchone()
        session['contaUsuario'] = contaUsuario[0]

        cur.execute("SELECT saldoBancario FROM users WHERE cpf = %s", [cpfLogin])
        saldoUsuario = cur.fetchone()
        session['saldoUsuario'] = saldoUsuario[0]

        #Laço. Se o cpfValidador e a senhaCriptografada forem varias:
        if not cpfValidador and not senhaCriptografada:
            #Primeira aparição de Flash. Um framework do Flask. Ele grava mensagens no cookie no navegador. Mostra a mensagem quando condicionada por um laço escrito em Python dentro do template em HTML que retorna no final da rota.
            flash("Preencha todos os campos!")
            #cpfValidados e senhaCriptografada recebem valor 1 ?
            cpfValidador = [1]
            senhaCriptografada = [1]
            return redirect (url_for('indexHome'))

        #Existe um bug aqui, ele não separa preencha o campo com cpf não existe no sistema.
        if cpfValidador[0] != cpfLogin:
            flash("CPF não existe no sistema!")
            return redirect (url_for('indexHome'))
        else:
            if check_password_hash(senhaCriptografada[0], senhaLogin):
                return redirect (url_for('deposito'))
            else:
                flash("Senha incorreta!")
                return redirect (url_for('indexHome'))
        
    return render_template("loginLeandro.html", error = error)

@app.route("/cadastro", methods=["GET", "POST"])
def indexCadastro():
    agenciaBancaria = "0001"
    saldoBancario = 0
    
#configurando a aquisicão das variaveis do formulario em HTML pelo request em Python
    if request.method == "POST":

        userDetails = request.form
        name = userDetails["nome"]
        cpf = userDetails["cpf"]
        dataAniversario = userDetails["dataAniversario"]
        genero = userDetails["genero"]
        endereco = userDetails["endereco"]        
        senha = userDetails["senha"]
        confirmacaoSenha = userDetails["confirmacaoSenha"]  
        senhaCriptografada = generate_password_hash(senha) 
        senhaCriptografada2 = None
        
         #critério preenchimento campos de senha
        if not name or not cpf or not dataAniversario or not genero or not endereco or not senha or not confirmacaoSenha:
            flash("Preencha todos os campos do formulário")
            return redirect (url_for("indexCadastro"))
        if senha == confirmacaoSenha:
            if check_password_hash(senhaCriptografada, senha):
                senhaCriptografada2 = senhaCriptografada
        else:
            flash("As senhas precisam ser iguais")
            return redirect (url_for("indexCadastro"))
        
        #gerador de conta bancaria automatico
        numero = []
        for i in range(1, 10):
            numero.append(random.randint(0, 9))
        contaBancaria="".join(map(str,numero))
               
        cur = mysql.connection.cursor()
        
        """ 
        #execução com bug
        #verificando se cpf já consta nos registros
        cur.execute("SELECT cpf FROM cadastro WHERE cpf = %s", [cpf])
        cpfValidator = cur.fetchone()
        if cpfValidator is not NULL:
            flash("CPF já cadastrado")
            return redirect (url_for("indexCadastro")) 
        """
        
        #salvando dados no BD e finalizando operação
        cur.execute("INSERT INTO users (agenciaBancaria, contaBancaria, saldoBancario, nome, cpf, dataAniversario, genero, endereco, senha, confirmacaoSenha) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", (agenciaBancaria, contaBancaria, saldoBancario, name, cpf, dataAniversario, genero, endereco, senhaCriptografada, senhaCriptografada2))
        mysql.connection.commit()
        cur.close()
        return redirect (url_for('indexHome'))
    return render_template("tela-cadastro.html")

#rota home
@app.route("/deposito", methods=["GET", "POST"])
def deposito():
    error = None
    if request.method == "POST":

        userDetails = request.form
        valorDeposito = userDetails["valorDeposito"]

        cur = mysql.connection.cursor()
        cur.execute("SELECT saldoBancario FROM users WHERE contaBancaria = %s", [session['contaUsuario']])
        saldoParcial = cur.fetchone()
        saldoFinal = saldoParcial[0]

        if int(valorDeposito) > 0:
            saldoFinal = int(saldoFinal) + int(valorDeposito)
            cur.execute("UPDATE users SET saldoBancario = %s", [saldoFinal])
            mysql.connection.commit()
            cur.close()
        else:
            flash("Apenas depósitos positivos e acima de R$: 0,00 são permitidos!")
            return redirect (url_for("deposito"))

        session.pop('saldoUsuario', None)
        session['saldoUsuario'] = saldoFinal
        return redirect (url_for('deposito'))

    return render_template("tela-deposito.html", error = error)

@app.route("/saque", methods=["GET", "POST"])
def saque():
    error = None
    if request.method == "POST":
        userDetails = request.form
        valorSaque = userDetails ['valorSaque']

        cur=mysql.connection.cursor()
        cur.execute("SELECT saldoBancario FROM users WHERE contaBancaria = %s",[session['contaUsuario']])
        saldoParcial = cur.fetchone()
        saldoFinal = saldoParcial[0]

        if  int(valorSaque) > 0 and int(valorSaque) <= int(saldoFinal):
            saldoFinal =int(saldoFinal) - int(valorSaque)
            cur.execute("UPDATE users SET saldoBancario = %s",[saldoFinal])
            mysql.connection.commit()
            cur.close()
        else:
            if int(valorSaque) <= 0:
                flash('Saques menores ou iguais a zero não são permitidos!')
                return redirect(url_for('saque'))
            
            if int(valorSaque) > int(saldoFinal):
                flash('Saldo indisponivel para esse valor')
                return redirect(url_for('saque'))

        session.pop('saldoUsuario', None)
        session['saldoUsuario'] = saldoFinal
        return redirect (url_for('saque'))

    return render_template("tela-saque.html", error = error)




""" @app.route("/saque", methods=["GET", "POST"])
def saque():
    return render_template("tela-saque.html") """

""" @app.route("/deposito", methods=["GET", "POST"])
def deposito():
    return render_template("tela-deposito.html") """

@app.route("/home", methods=["GET", "POST"])
def home():
    return render_template("tela-home.html")

@app.route("/transferencia", methods=["GET", "POST"])
def transferencia():
    return render_template("tela-transferencia.html")

@app.route("/extrato", methods=["GET", "POST"])
def extrato():
    return render_template("tela-extrato.html")

@app.route("/configuracoes", methods=["GET", "POST"])
def configuracoes():
    return render_template("tela-configuracoes.html")

app.run(debug=True) #comando inicia automaticamente o programa, habilitando o debug sempre que algo for atualizado!