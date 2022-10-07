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
    session["usuarioLogado"] = False
    #Inicializando as variaveis. None = Vazias, até que elas recebam outro valor.
    error = None

    #Inicialização dos componentes de indexHome, caso o método utilizado seja POST. Ou seja, se o usuário clicar em enviar informações ao Servidor.
    if request.method == "POST":

        #userDetails é uma variável que carregará o request.form do Flask: request.
        userDetails = request.form

        #Todas as vezes que userDetails receber entre caixas uma variável, como abaixo, ele está recebendo informações das quais o usuário digitou em algum formulario do Template HTML que está retornando no final do def indexHome.
        numContaUsuario = userDetails["numContaUsuario"]
        senhaLogin = userDetails["senhaLogin"]

        #Aqui verifico se as variáveis numContaUsuario e senhaLogin possuem alguma informação nelas. É importante que fique aqui para evitar que erros ocorram no seguimento do código. Prende o usuário na tela de Login caso os campos estejam vazios.
        if not numContaUsuario or not senhaLogin:
            #Primeira aparição de Flash. Um framework do Flask. Ele grava mensagens no cookie no navegador. Mostra a mensagem quando condicionada por um laço escrito em Python dentro do template em HTML que retorna no final da rota.
            flash("Preencha todos os campos!")
            return redirect (url_for('indexHome'))

        #Aqui está um try, exception. Caso essas variáveis tenham resultado válido ao retornar do banco de dados, se estiver correto o código parte para testar a senha. Se não ele fica preso na tela de login.
        try:
            #Inicilizando o MySQL, através da variável cur. Se não iniciar ele retorna cursor fechado!
            cur = mysql.connection.cursor()
            #Pedindo ao SQL que execute a linha de código a seguir. Selecionar uma das colunas da tabela users onde o cpf seja um valor igual a "%s", e por "%s" ele entende que seja o que estiver na variável cpfLogin.
            cur.execute("SELECT senha, user_id, contaBancaria, nome, agenciaBancaria, saldoBancario FROM users WHERE contaBancaria = %s", [numContaUsuario])
            #O resultado da query acima será "capturado" através de fetchone() dentro da variável senhaCriptografada. Parece que ao ser capturado o resultado vira uma lista.
            retornoContaUsuario = cur.fetchone()
            senhaCriptografada = retornoContaUsuario[0]
            session['idUsuario'] = retornoContaUsuario[1]
            session['contaUsuario'] = retornoContaUsuario[2]
            session['nomeUsuario'] = retornoContaUsuario[3]
            session['agenciaUsuario'] = retornoContaUsuario[4]
            session['saldoUsuario'] = retornoContaUsuario[5]
        except Exception as ex:
             flash("Conta Bancária não existe no sistema! Cadastre-se para continuar.")
             return render_template("tela-login.html")
        
        #Se o contaValidador e a senhaCriptografada estiverem corretos ele loga, se não fica preso na tela de Login:
        if check_password_hash(senhaCriptografada, senhaLogin):
            session.pop('usuarioLogado', None)
            session["usuarioLogado"] = True
            return redirect (url_for('home'))
        else:
            flash("Senha incorreta!")
            return render_template("tela-login.html")

    return render_template("tela-login.html", error = error)

#Rota da página cadastro
@app.route("/cadastro", methods=["GET", "POST"])
def indexCadastro():
    #Inicializando algumas variaveis importantes pro resto da função indexCadastro. A variável agenciaBancaria recebe por enquanto uma string "0001". O saldoBancario sempre começa com 0 Reias.
    agenciaBancaria = "0001"
    saldoBancario = 0.00
    cadastro = False
    voltarLogin = False
    
    #Configurando a aquisicão das variaveis do formulario em HTML pelo request em Python (metódo POST)
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
        checkboxConsentimentoUsuario = request.form.get("consentimentoUsuario")

        app.logger.info(checkboxConsentimentoUsuario)

        #Critério preenchimento campos do cadastro, incluindo as duas senhas, que precisam ser iguais para que ela seja transformada em Hash criptografado e seja mandado pro banco de dados protegida.
        if not name or not cpf or not dataAniversario or not genero or not endereco or not senha or not confirmacaoSenha:
            flash("Preencha todos os campos do formulário")
            return redirect (url_for("indexCadastro"))

        try:
            #Verificando se cpf já consta nos registros durante o cadastro
            cur = mysql.connection.cursor()
            cur.execute("SELECT cpf FROM users WHERE cpf = %s", [cpf])
            cpfUsuario = cur.fetchone()
            retornoCpfUsuario = cpfUsuario[0]
        except Exception as ex:
            retornoCpfUsuario = None
            
        if retornoCpfUsuario and retornoCpfUsuario != None:
            flash("CPF já cadastrado")
            return redirect (url_for("indexCadastro"))


        if senha == confirmacaoSenha:
            if check_password_hash(senhaCriptografada, senha):
                senhaCriptografada2 = senhaCriptografada
        else:
            flash("As senhas precisam ser iguais")
            return redirect (url_for("indexCadastro"))

        if checkboxConsentimentoUsuario == None:
            flash("Aceite os Termos de Uso e Política de Privacidade.")
            return redirect (url_for("indexCadastro"))

        #Gerador de conta bancaria automatico
        numero = []
        for i in range(1, 10):
            numero.append(random.randint(0, 9))
        contaBancaria="".join(map(str,numero))
        
        #Salvando dados no BD e finalizando operação
        
        
        cur.execute("INSERT INTO users (agenciaBancaria, contaBancaria, saldoBancario, nome, cpf, dataAniversario, genero, endereco, senha, confirmacaoSenha) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", (agenciaBancaria, contaBancaria, saldoBancario, name, cpf, dataAniversario, genero, endereco, senhaCriptografada, senhaCriptografada2))
        mysql.connection.commit()
        cur.close()
        cadastro = True

        #Lógica para retornar usuário ao Login pós Cadastro e mostrar o numero da sua conta bancaria para Logar.
        if cadastro == True:
            cur = mysql.connection.cursor()
            cur.execute("SELECT contaBancaria FROM users WHERE cpf = %s", [cpf])
            contaUsuario = cur.fetchone()
            session['contaUsuario'] = contaUsuario[0]
            flash(f"Cadastro criado com sucesso!\nATENÇÃO! Para logar você precisa da sua Conta Bancária, anote-a:\n {str(session.get('contaUsuario'))}")
            if request.method == "POST":
                voltarLogin = True
                if voltarLogin == True:
                    return redirect (url_for('indexHome'))
        else:
            flash("Algo deu errado com seu cadastro, tente novamente e atente-se aos campos e senha!")
            return redirect (url_for('indexCadastro'))


    return render_template("tela-cadastro.html")



#Rota home
@app.route("/deposito", methods=["GET", "POST"])
def deposito():
    if session["usuarioLogado"] == False:
        return redirect (url_for("indexHome"))
    error = None
    if request.method == "POST":

        userDetails = request.form
        valorDeposito = userDetails["valorDeposito"]

        cur = mysql.connection.cursor()
        cur.execute("SELECT saldoBancario FROM users WHERE contaBancaria = %s", [session['contaUsuario']])
        saldoParcial = cur.fetchone()
        saldoFinal = saldoParcial[0]

        #Onde antes tinha int troquei pra float para que o depósito e saque de moedas seja permitido.
        if valorDeposito and float(valorDeposito) > 0:
            saldoFinal = float(saldoFinal) + float(valorDeposito)
            #Para fazer UPDATES onde preciso que o duas variaveis precisam ser mudadas, basta utilizar o %s. Entretanto, no final como é uma Tupla, preciso informar o que substituir por meio de um parênteses EX:([x],[y]).
            cur.execute("UPDATE users SET saldoBancario = %s WHERE user_id= %s", ([saldoFinal], session['idUsuario']))
            mysql.connection.commit()
            cur.close()
            flash("Depósito realizado com sucesso!")
        else:
            flash("Apenas depósitos positivos e acima de R$ 0,00 são permitidos!")
            return redirect (url_for("deposito")) 

        #session.pop remove os dados de 'saldoUsuario'. Em seguida pedi para que o saldo final sofresse uma formatação e ficasse com duas casas após a vírgula. depois renovei o session 'saldoUsuario' para pegar o saldo formatado. Precisei excluir e pegar novamente para atualizar o cache.
        session.pop('saldoUsuario', None)
        saldoFormatado = '{0:.2f}'.format(saldoFinal)
        session['saldoUsuario'] = saldoFormatado.replace('.',',')
        return redirect (url_for('deposito'))

    return render_template("tela-deposito.html", error = error)



@app.route("/saque", methods=["GET", "POST"])
def saque():
    if session["usuarioLogado"] == False:
        return redirect (url_for("indexHome"))
    error = None
    if request.method == "POST":
        userDetails = request.form
        valorSaque = userDetails ['valorSaque']

        cur=mysql.connection.cursor()
        cur.execute("SELECT saldoBancario FROM users WHERE contaBancaria = %s",[session['contaUsuario']])
        saldoParcial = cur.fetchone()
        saldoFinal = saldoParcial[0]

        #Onde antes tinha int troquei pra float para que o depósito e saque de moedas seja permitido.
        if  valorSaque and float(valorSaque) > 0 and float(valorSaque) <= float(saldoFinal):
            saldoFinal = float(saldoFinal) - float(valorSaque)
            cur.execute("UPDATE users SET saldoBancario = %s WHERE user_id= %s", ([saldoFinal], session['idUsuario']))
            mysql.connection.commit()
            cur.close()
            flash("Saque realizado com sucesso!")
        else:
            if valorSaque and float(valorSaque) <= 0:
                flash('Apenas saques positivos e acima de R$ 0,00 são permitidos!')
                return redirect(url_for('saque'))
            
            if valorSaque and float(valorSaque) > float(saldoFinal):
                flash('Saldo indisponivel para esse valor')
                return redirect(url_for('saque'))
            else:
                flash('Preencha o campo Valor, para realizar o saque!')
                return redirect(url_for('saque'))

        session.pop('saldoUsuario', None)
        saldoFormatado = '{0:.2f}'.format(saldoFinal)
        session['saldoUsuario'] = saldoFormatado.replace('.',',')
        return redirect (url_for('saque'))

    return render_template("tela-saque.html", error = error)

#Rota para logout. Se o usuário clicar em sair nas páginas da Home, sua sessão é limpa, apagando todos os dados do cache do navegador. Ele é redirecionado à tela de Login e uma mensagem aparece informando que o Usuário foi deslogado.
@app.route("/logout", methods=["GET","POST"])
def logout():
    for sessions in list(session.keys()):
        session.pop(sessions)
    session.pop('usuarioLogado', None)
    session["usuarioLogado"] = False
    flash("Usuário deslogado com sucesso!")
    return redirect (url_for("indexHome"))


@app.route("/home", methods=["GET", "POST"])
def home():
    if session["usuarioLogado"] == False:
        return redirect (url_for("indexHome"))
    return render_template("tela-home.html")

#Rotas Transferencia, Extrato, Configurações inicializadas. Mas ainda sem função.
@app.route("/transferencia", methods=["GET", "POST"])
def transferencia():
    return render_template("tela-abertura-de-conta.html")

@app.route("/extrato", methods=["GET", "POST"])
def extrato():
    return render_template("tela-extrato.html")

@app.route("/configuracoes", methods=["GET", "POST"])
def configuracoes():
    return render_template("tela-configuracoes.html")

@app.route("/abertura", methods=["GET", "POST"])
def abertura():
    return render_template("tela-abertura-de-conta.html")
 
#Comando inicia automaticamente o programa, habilitando o debug sempre que algo for atualizado!
app.run(debug=True)