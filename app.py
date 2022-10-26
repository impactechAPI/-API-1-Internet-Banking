from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash, check_password_hash
import yaml
import random
import pandas as pd
from datetime import datetime

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

#Configuração de Hora do Sistema - OBS: Tem que ser realocado para um arquivo JSON
def dataAgora():
    data = datetime.now().strftime("%d/%m/%Y")
    return data

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

        #Aqui está um try, exception. Caso essas variáveis tenham resultado válido ao retornar do banco de dados, se estiver correto, o código parte para testar a senha. Se não, ele fica preso na tela de login.
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

            cur.execute("SELECT statusSolicitacao from confirmacaoAbertura where contaBancaria = %s", ([numContaUsuario]))
            retornoStatusSolicitacao = cur.fetchone()
            statusSolicitacao = retornoStatusSolicitacao[0] 

        except Exception as ex:
             flash("Conta não existe no sistema! Cadastre-se para continuar.")
             return render_template("login_cliente.html", tituloNavegador="Bem-vindo!")
        
        #Se a senhaCriptografada estiverem corretos ele loga, se não fica preso na tela de Login:
        if check_password_hash(senhaCriptografada, senhaLogin):
            #Session.pop apaga o conteúdo localizado dentro da variável que está entre aspas, dentro do parêntesis.
            session.pop('usuarioLogado', None)
            session["usuarioLogado"] = True
            #Teste de status da solicitação de cadastro.
            if statusSolicitacao == "Pendente":
                flash("A sua abertura de conta ainda está para ser avaliada por um de nossos gerentes, por favor aguarde!")
                return redirect (url_for('indexHome'))
            elif statusSolicitacao == "Confirmada":
                return redirect (url_for('home'))
            else:
                flash("Infelizmente, algo não saiu como esperado em seu cadastro. Não se preocupe, tente novamente se atentando ao registro de seus dados, nós faremos outra avaliação para você!")
                return redirect (url_for('indexHome'))
        else:
            flash("Senha incorreta!")
            return render_template("login_cliente.html", tituloNavegador="Bem-vindo!")

    return render_template("login_cliente.html", tituloNavegador="Bem-vindo!", error = error)

#Rota da página cadastro
@app.route("/cadastro", methods=["GET", "POST"])
def indexCadastro():
    #Inicializando algumas variaveis importantes pro resto da função indexCadastro. A variável agenciaBancaria recebe por enquanto uma string "0001". O saldoBancario sempre começa com 0 Reais.
    agenciaBancaria = "0001"
    # !! Talvez dê para mudar o ponto por vírgula usando replace() !!
    saldoBancario = "0.00"
    cadastro = False
    voltarLogin = False
    statusSolicitacao = "Pendente"
    
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
        tipoSolicitacao = "Abertura"
        ultimaTransacao = 0

        #Pega o bool que retorna do checkbox do consentimento do usuário
        checkboxConsentimentoUsuario = request.form.get("consentimentoUsuario")

        #app.logger.info printa a variável que está dentro do parêntesis.
        app.logger.info(checkboxConsentimentoUsuario)

        #Critério preenchimento campos do cadastro, incluindo as duas senhas, que precisam ser iguais para que ela seja transformada em Hash criptografado e seja mandado pro banco de dados protegida.
        if not name or not cpf or not dataAniversario or not genero or not endereco or not senha or not confirmacaoSenha:
            flash("Preencha todos os campos do formulário!")
            return redirect (url_for("indexCadastro"))

        #ATENÇÃO! trecho retirado não descomentar por enquanto
        """ try:
            #Verificando se cpf já consta nos registros durante o cadastro !! Não deve ser feito mais !!
            cur = mysql.connection.cursor()
            cur.execute("SELECT cpf FROM users WHERE cpf = %s", [cpf])
            cpfUsuario = cur.fetchone()
            retornoCpfUsuario = cpfUsuario[0]
        except Exception as ex:
            retornoCpfUsuario = None
         
            if retornoCpfUsuario and retornoCpfUsuario != None:
            flash("CPF já cadastrado")
            return redirect (url_for("indexCadastro")) 
        """

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

        session.pop("horaSistema", None)
        session["horaSistema"] = dataAgora()
        
        #Salvando dados no BD e finalizando operação
        mysql.connection.commit()
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO users (agenciaBancaria, contaBancaria, saldoBancario, nome, cpf, dataAniversario, genero, endereco, senha, confirmacaoSenha) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", (agenciaBancaria, contaBancaria, saldoBancario, name, cpf, dataAniversario, genero, endereco, senhaCriptografada, senhaCriptografada2))
        
        mysql.connection.commit()

        cur.close()
        cadastro = True

        #Lógica para retornar usuário ao Login pós Cadastro e mostrar o numero da sua conta bancaria para Logar.
        if cadastro == True:
            cur = mysql.connection.cursor()
            cur.execute("SELECT contaBancaria FROM users WHERE nome = %s and cpf = %s", ([name], [cpf]))
            contaUsuario = cur.fetchone()
            session['contaUsuario'] = contaUsuario[0]

            cur.execute("UPDATE gerenciamentoUsuarios set ultimaTransacao = 0 where tipoSolicitacao = %s", ([tipoSolicitacao]))

            ultimaTransacao = 1

            cur.execute("SELECT user_id FROM users WHERE contaBancaria = %s", ([session['contaUsuario']]))
            retornoidUsuarioCadastro = cur.fetchone()
            solicitacaoidUsuarioCadastrado = retornoidUsuarioCadastro[0]

            cur.execute("INSERT INTO gerenciamentoUsuarios (dataHoraSolicitacao, tipoSolicitacao, usuarioDaSolicitacao, ultimaTransacao, user_id) VALUES(%s, %s, %s, %s, %s)", (session['horaSistema'], [tipoSolicitacao], [name], [ultimaTransacao], [solicitacaoidUsuarioCadastrado]))
            mysql.connection.commit()

            cur.execute("SELECT solicitacao_id from gerenciamentoUsuarios where ultimaTransacao = %s and tipoSolicitacao = %s", ([ultimaTransacao], [tipoSolicitacao]))
            retornoSolicitacaoId = cur.fetchone()
            solicitacaoId = retornoSolicitacaoId[0] 

            cur.execute("INSERT INTO confirmacaoAbertura (nome, cpf, dataAniversario, genero, endereco, contaBancaria, agenciaBancaria, user_id, statusSolicitacao, solicitacao_id) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", ([name], [cpf], [dataAniversario], [genero], [endereco], [contaBancaria], [agenciaBancaria], [solicitacaoidUsuarioCadastrado], [statusSolicitacao], [solicitacaoId]))
            mysql.connection.commit()
            cur.close()

            flash(f"Cadastro criado com sucesso!\nATENÇÃO! Para entrar você precisa do nº de sua Conta, anote-a por segurança:\n {str(session.get('contaUsuario'))}")
            if request.method == "POST":
                voltarLogin = True
                if voltarLogin == True:
                    return redirect (url_for('indexHome'))
        else:
            flash("Algo deu errado com seu cadastro, tente novamente e atente-se aos campos e senha!")
            return redirect (url_for('indexCadastro'))

    return render_template("cadastro.html", tituloNavegador="Novo Cliente")

#Rota home
@app.route("/deposito", methods=["GET", "POST"])
def deposito():
    if session["usuarioLogado"] == False:
        return redirect (url_for("indexHome"))

    error = None
    tipoSolicitacao = "Depósito"
    session["tipoSolicitacao"] = tipoSolicitacao
    ultimaTransacao = 0

    if request.method == "POST":

        userDetails = request.form
        valorDeposito = userDetails["valorDeposito"]
        session["valorDeposito"] = valorDeposito

        cur = mysql.connection.cursor()
        cur.execute("SELECT saldoBancario FROM users WHERE contaBancaria = %s", [session['contaUsuario']])
        saldoAtual = cur.fetchone()
        saldoAtual = saldoAtual[0]
        session["saldoUsuarioAntes"] = saldoAtual

        #Onde antes tinha int troquei pra float para que o depósito e saque de moedas seja permitido.
        if valorDeposito and float(valorDeposito) > 0:
            saldoFinalConfirmacao = float(saldoAtual) + float(valorDeposito)
            session["saldoFinalConfirmacao"] = saldoFinalConfirmacao

            session.pop("horaSistema", None)
            session["horaSistema"] = dataAgora()

            cur.execute("UPDATE gerenciamentoUsuarios set ultimaTransacao = 0 where tipoSolicitacao = %s", ([tipoSolicitacao]))

            ultimaTransacao = 1

            cur.execute("INSERT INTO gerenciamentoUsuarios (dataHoraSolicitacao, tipoSolicitacao, usuarioDaSolicitacao, ultimaTransacao, user_id) VALUES(%s, %s, %s, %s, %s)", (session['horaSistema'], [tipoSolicitacao], session["nomeUsuario"], [ultimaTransacao], session["idUsuario"]))
            mysql.connection.commit()

            cur.execute("SELECT solicitacao_id from gerenciamentoUsuarios where ultimaTransacao = %s and tipoSolicitacao = %s", ([ultimaTransacao], [tipoSolicitacao]))
            retornoSolicitacaoId = cur.fetchone()
            solicitacaoId = retornoSolicitacaoId[0]    

            cur.execute("INSERT INTO confirmacaoDeposito (nome, contaBancaria, agenciaBancaria, saldoAtual, valorDeposito, saldoFinal, user_id, solicitacao_id) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)", (session["nomeUsuario"], session["contaUsuario"], session["agenciaUsuario"], [saldoAtual], [valorDeposito], [saldoFinalConfirmacao], session["idUsuario"], [solicitacaoId]))
            mysql.connection.commit()

            cur.close()

            flash("Depósito realizado. Aguarde a confirmação do depósito pelo Gerente de sua agência! Para ver seu comprovante clique ")
        else:
            flash("Apenas depósitos positivos e acima de R$ 0,00 são permitidos!")
            return redirect (url_for("deposito"))

        #session.pop remove os dados de 'saldoUsuario'. Em seguida pedi para que o saldo final sofresse uma formatação e ficasse com duas casas após a vírgula. depois renovei o session 'saldoUsuario' para pegar o saldo formatado. Precisei excluir e pegar novamente para atualizar o cache.
        session.pop('saldoUsuario', None)
        saldoFormatado = '{0:.2f}'.format(saldoAtual)
        session['saldoUsuario'] = saldoFormatado.replace('.',',')
        return redirect (url_for('deposito'))

    return render_template("tela-deposito.html", titulo="Depósito", error = error)

#Rota para página saque.
@app.route("/saque", methods=["GET", "POST"])
def saque():
    if session["usuarioLogado"] == False:
        return redirect (url_for("indexHome"))


    error = None
    tipoMovimentacao = "Saque"
    session["tipoSolicitacao"] = tipoMovimentacao
    

    if request.method == "POST":
        userDetails = request.form
        valorSaque = userDetails ['valorSaque']
        session["valorDeposito"] = valorSaque

        cur = mysql.connection.cursor()
        cur.execute("SELECT saldoBancario FROM users WHERE contaBancaria = %s",[session['contaUsuario']])
        saldoParcial = cur.fetchone()
        saldoParcial = saldoParcial[0]
        session["saldoUsuarioAntes"] = saldoParcial

        #Onde antes tinha int troquei pra float para que o depósito e saque de moedas seja permitido.
        if  valorSaque and float(valorSaque) > 0:
            saldoFinal = float(saldoParcial) - float(valorSaque)
            session["saldoFinalConfirmacao"] = saldoFinal
            
            session.pop("horaSistema", None)
            session["horaSistema"] = dataAgora()
            cur.execute("UPDATE users SET saldoBancario = %s WHERE user_id= %s", ([saldoFinal], session['idUsuario']))
            cur.execute("INSERT INTO movimentacaoConta (dataHoraMovimentacao, tipoMovimentacao, movimentacao, user_id) VALUES (%s, %s, %s, %s)", (session['horaSistema'], [tipoMovimentacao], [valorSaque], session['idUsuario']))
            mysql.connection.commit()
            cur.close()
            flash("Saque realizado com sucesso! Para ver seu comprovante clique ")
        else:
            if valorSaque and float(valorSaque) <= 0:
                flash('Apenas saques acima de R$ 0,00 são permitidos!')
                return redirect(url_for('saque'))
            if not valorSaque:
                flash('Preencha o campo Valor, para realizar o saque!')
                return redirect(url_for('saque'))

        session.pop('saldoUsuario', None)
        saldoFormatado = '{0:.2f}'.format(saldoFinal)
        session['saldoUsuario'] = saldoFormatado.replace('.',',')
        return redirect (url_for('saque'))

    return render_template("tela-saque.html", titulo="Saque", error = error)

@app.route("/comprovante", methods=["GET", "POST"])
def comprovante():

    return render_template("tela-comprovante.html", titulo="Comprovante")

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
    session['horaSistema'] = dataAgora()
    return render_template("tela-home.html")

#Rotas Transferencia, Extrato, Configurações inicializadas. Mas ainda sem função.
@app.route("/transferencia", methods=["GET", "POST"])
def transferencia():
    return render_template("tela-abertura-de-conta.html")

#Rota da página Extrato
@app.route("/extrato", methods=["GET", "POST"])
def extrato():
    #Se a sessão do Usuario for Falsa, a rota deve voltar para indexHome
    if session["usuarioLogado"] == False:
        return redirect (url_for("indexHome"))
    
    #Se o usuario clicar em Pesquisar retorna ao HTML a tabela contendo o conteúdo pesquisado.
    if request.method == "POST":
        if "pesquisar" in request.form:
            session.pop("cacheApagado", None)
            session["cacheApagado"] = None
            #O type date do HTML retorna o form do usuario no formato YYYY-MM-DD, foi preciso alterar "-" por "/" e "ano" por "dia"
            dataMovimentacaoInicial = request.form.get("data-inicial")
            dataMovimentacaoInicial = dataMovimentacaoInicial[-2:] + dataMovimentacaoInicial[4:8] + dataMovimentacaoInicial[0:4]
            dataMovimentacaoInicial = dataMovimentacaoInicial.replace("-","/")
            session["dataMovimentacaoInicialCache"] = dataMovimentacaoInicial
            #O type date do HTML retorna o form do usuario no formato YYYY-MM-DD, foi preciso alterar "-" por "/" e "ano" por "dia"
            dataMovimentacaoLimite = request.form.get("data-limite")
            dataMovimentacaoLimite = dataMovimentacaoLimite[-2:] + dataMovimentacaoLimite[4:8] + dataMovimentacaoLimite[0:4]
            dataMovimentacaoLimite = dataMovimentacaoLimite.replace("-","/")
            session["dataMovimentacaoLimiteCache"] = dataMovimentacaoLimite
            #Estava retornando deposito, sem acento, acrescentei o acento pois será feito um query no DB através dessa variável
            tipoTransacao = request.form.get("tipo-transacao")
            if tipoTransacao == "deposito":
                tipoTransacao = tipoTransacao[0:3] + "ó" + tipoTransacao[4:]
                session["tipoTransacaoCache"] = tipoTransacao
            session["tipoTransacaoCache"] = tipoTransacao

            #Pegando as variaveis do Banco de Dados segundo os dados informados pelo Usuário x

            #Se houver dados em dataMovimentacao e não houver em tipoTransacao, mostrar a dataMovimentacao selecionada para todos os tipos de Transacao
            if dataMovimentacaoInicial and dataMovimentacaoLimite and tipoTransacao == "todos":
                cur = mysql.connection.cursor()
                cur.execute("SELECT dataHoraMovimentacao, movimentacao, tipoMovimentacao FROM movimentacaoConta WHERE user_id = %s AND dataHoraMovimentacao >= %s AND dataHoraMovimentacao <= %s", (session['idUsuario'], [dataMovimentacaoInicial], [dataMovimentacaoLimite]))

                dataMovimentacao = []
                movimentacao = []
                tipoMovimentacao = []

                for i in cur:
                    dataMovimentacao.append(i[0])
                    movimentacao.append(i[1])
                    tipoMovimentacao.append(i[2])

                tabelaMovimentacao = pd.DataFrame(list(zip(dataMovimentacao, movimentacao, tipoMovimentacao)), columns =['Data','Movimentação', 'Tipo de Movimentação'])

                return render_template("tela-extrato.html", titulo="Extrato", tabelas=[tabelaMovimentacao.to_html(index=False)], titulos=tabelaMovimentacao.columns.values)

            #Se a dataMovimentacao e o tipoTransacao forem especificados, mostrar a dataMovimentacao e o tipo de Transacao especificado
            elif dataMovimentacaoInicial and dataMovimentacaoLimite and tipoTransacao != "todos":
                cur = mysql.connection.cursor()
                cur.execute("SELECT dataHoraMovimentacao, movimentacao, tipoMovimentacao FROM movimentacaoConta WHERE user_id = %s AND dataHoraMovimentacao >= %s AND dataHoraMovimentacao <= %s AND tipoMovimentacao = %s", (session['idUsuario'], [dataMovimentacaoInicial], [dataMovimentacaoLimite], [tipoTransacao]))

                dataMovimentacao = []
                movimentacao = []
                tipoMovimentacao = []

                for i in cur:
                    dataMovimentacao.append(i[0])
                    movimentacao.append(i[1])
                    tipoMovimentacao.append(i[2])

                tabelaMovimentacao = pd.DataFrame(list(zip(dataMovimentacao, movimentacao, tipoMovimentacao)), columns =['Data','Movimentação', 'Tipo de Movimentação'])

                return render_template("tela-extrato.html", titulo="Extrato", tabelas=[tabelaMovimentacao.to_html(index=False)], titulos=tabelaMovimentacao.columns.values)

            #Se não for especificado nenhum dado para dataMovimentacao, mas ser para o tipoTransacao, mostrar todos os dados do tipoTransacao em todas as datas
            elif not dataMovimentacaoInicial and not dataMovimentacaoLimite and tipoTransacao != "todos":
                cur = mysql.connection.cursor()
                cur.execute("SELECT dataHoraMovimentacao, movimentacao, tipoMovimentacao FROM movimentacaoConta WHERE user_id = %s AND tipoMovimentacao = %s", (session['idUsuario'], [tipoTransacao]))

                dataMovimentacao = []
                movimentacao = []
                tipoMovimentacao = []

                for i in cur:
                    dataMovimentacao.append(i[0])
                    movimentacao.append(i[1])
                    tipoMovimentacao.append(i[2])

                tabelaMovimentacao = pd.DataFrame(list(zip(dataMovimentacao, movimentacao, tipoMovimentacao)), columns =['Data','Movimentação', 'Tipo de Movimentação'])

                return render_template("tela-extrato.html", titulo="Extrato", tabelas=[tabelaMovimentacao.to_html(index=False)], titulos=tabelaMovimentacao.columns.values)

            elif not dataMovimentacaoInicial and not dataMovimentacaoLimite and tipoTransacao == "todos" and session["cacheApagado"] == None:
                #session.pop('saldoUsuario', None)
                cur = mysql.connection.cursor()
                cur.execute("SELECT dataHoraMovimentacao, movimentacao, tipoMovimentacao FROM movimentacaoConta WHERE user_id = %s AND dataHoraMovimentacao >= %s AND dataHoraMovimentacao <= %s AND tipoMovimentacao = %s", (session['idUsuario'], session["dataMovimentacaoInicialCache"], session["dataMovimentacaoLimiteCache"], session["tipoTransacaoCache"]))

                dataMovimentacao = []
                movimentacao = []
                tipoMovimentacao = []

                for i in cur:
                    dataMovimentacao.append(i[0])
                    movimentacao.append(i[1])
                    tipoMovimentacao.append(i[2])

                tabelaMovimentacao = pd.DataFrame(list(zip(dataMovimentacao, movimentacao, tipoMovimentacao)), columns =['Data','Movimentação', 'Tipo de Movimentação'])

                return render_template("tela-extrato.html", titulo="Extrato", tabelas=[tabelaMovimentacao.to_html(index=False)], titulos=tabelaMovimentacao.columns.values)

            elif not dataMovimentacaoInicial and not dataMovimentacaoLimite and tipoTransacao == "todos" and session["cacheApagado"] == True:
                cur = mysql.connection.cursor()
                cur.execute("SELECT dataHoraMovimentacao, movimentacao, tipoMovimentacao FROM movimentacaoConta WHERE user_id = %s", [session['idUsuario']])

                dataMovimentacao = []
                movimentacao = []
                tipoMovimentacao = []

                for i in cur:
                    dataMovimentacao.append(i[0])
                    movimentacao.append(i[1])
                    tipoMovimentacao.append(i[2])

                tabelaMovimentacao = pd.DataFrame(list(zip(dataMovimentacao, movimentacao, tipoMovimentacao)), columns = ['Data','Movimentação', 'Tipo de Movimentação'])

                return render_template("tela-extrato.html", titulo="Extrato", tabelas=[tabelaMovimentacao.to_html(index=False)], titulos=tabelaMovimentacao.columns.values)

        if "imprimir" in request.form:
            #O type date do HTML retorna o form do usuario no formato YYYY-MM-DD, foi preciso alterar "-" por "/" e "ano" por "dia"
            dataMovimentacaoInicial = request.form.get("data-inicial")
            dataMovimentacaoInicial = dataMovimentacaoInicial[-2:] + dataMovimentacaoInicial[4:8] + dataMovimentacaoInicial[0:4]
            dataMovimentacaoInicial = dataMovimentacaoInicial.replace("-","/")
            session["dataMovimentacaoInicialCache"] = dataMovimentacaoInicial
            #O type date do HTML retorna o form do usuario no formato YYYY-MM-DD, foi preciso alterar "-" por "/" e "ano" por "dia"
            dataMovimentacaoLimite = request.form.get("data-limite")
            dataMovimentacaoLimite = dataMovimentacaoLimite[-2:] + dataMovimentacaoLimite[4:8] + dataMovimentacaoLimite[0:4]
            dataMovimentacaoLimite = dataMovimentacaoLimite.replace("-","/")
            session["dataMovimentacaoLimiteCache"] = dataMovimentacaoLimite
            #Estava retornando deposito, sem acento, acrescentei o acento pois será feito um query no DB através dessa variável
            tipoTransacao = request.form.get("tipo-transacao")
            session["tipoTransacaoCache"] = tipoTransacao
            if tipoTransacao == "deposito":
                tipoTransacao = tipoTransacao[0:3] + "ó" + tipoTransacao[4:]
                session["tipoTransacaoCache"] = tipoTransacao
            session["tipoTransacaoCache"] = tipoTransacao

            app.logger.info(str(session["dataMovimentacaoInicialCache"]), str(session["dataMovimentacaoLimiteCache"]), str(session["tipoTransacaoCache"]))

            #Pegando as variaveis do Banco de Dados segundo os dados informados pelo Usuário x

            if dataMovimentacaoInicial and dataMovimentacaoLimite and tipoTransacao == "todos":
                cur = mysql.connection.cursor()
                cur.execute("SELECT dataHoraMovimentacao, movimentacao, tipoMovimentacao FROM movimentacaoConta WHERE user_id = %s AND dataHoraMovimentacao >= %s AND dataHoraMovimentacao <= %s", (session['idUsuario'], [dataMovimentacaoInicial], [dataMovimentacaoLimite]))

                dataMovimentacao = []
                movimentacao = []
                tipoMovimentacao = []

                for i in cur:
                    dataMovimentacao.append(i[0])
                    movimentacao.append(i[1])
                    tipoMovimentacao.append(i[2])

                tabelaMovimentacao = pd.DataFrame(list(zip(dataMovimentacao, movimentacao, tipoMovimentacao)), columns = ['Data','Movimentação', 'Tipo de Movimentação'])

                tabelaMovimentacao.to_csv(r'extrato.txt', header=True, index=False, sep='\t', mode='a')

                return render_template("tela-extrato.html", titulo="Extrato", tabelas=[tabelaMovimentacao.to_html(index=False)], titulos=tabelaMovimentacao.columns.values)

            elif dataMovimentacaoInicial and dataMovimentacaoLimite and tipoTransacao != "todos":
                cur = mysql.connection.cursor()
                cur.execute("SELECT dataHoraMovimentacao, movimentacao, tipoMovimentacao FROM movimentacaoConta WHERE user_id = %s AND dataHoraMovimentacao >= %s AND dataHoraMovimentacao <= %s AND tipoMovimentacao = %s", (session['idUsuario'], [dataMovimentacaoInicial], [dataMovimentacaoLimite], [tipoTransacao]))

                dataMovimentacao = []
                movimentacao = []
                tipoMovimentacao = []

                for i in cur:
                    dataMovimentacao.append(i[0])
                    movimentacao.append(i[1])
                    tipoMovimentacao.append(i[2])

                tabelaMovimentacao = pd.DataFrame(list(zip(dataMovimentacao, movimentacao, tipoMovimentacao)), columns = ['Data','Movimentação', 'Tipo de Movimentação'])

                tabelaMovimentacao.to_csv(r'extrato.txt', header=True, index=False, sep='\t', mode='a')

                return render_template("tela-extrato.html", titulo="Extrato", tabelas=[tabelaMovimentacao.to_html(index=False)], titulos=tabelaMovimentacao.columns.values)

            elif not dataMovimentacaoInicial and not dataMovimentacaoLimite and tipoTransacao != "todos":
                cur = mysql.connection.cursor()
                cur.execute("SELECT dataHoraMovimentacao, movimentacao, tipoMovimentacao FROM movimentacaoConta WHERE user_id = %s AND tipoMovimentacao = %s", (session['idUsuario'], [tipoTransacao]))

                dataMovimentacao = []
                movimentacao = []
                tipoMovimentacao = []

                for i in cur:
                    dataMovimentacao.append(i[0])
                    movimentacao.append(i[1])
                    tipoMovimentacao.append(i[2])

                tabelaMovimentacao = pd.DataFrame(list(zip(dataMovimentacao, movimentacao, tipoMovimentacao)), columns = ['Data','Movimentação', 'Tipo de Movimentação'])

                tabelaMovimentacao.to_csv(r'extrato.txt', header=True, index=False, sep='\t', mode='a')

                return render_template("tela-extrato.html", titulo="Extrato", tabelas=[tabelaMovimentacao.to_html(index=False)], titulos=tabelaMovimentacao.columns.values)

            elif not dataMovimentacaoInicial and not dataMovimentacaoLimite and tipoTransacao == "todos" and session["cacheApagado"] == None:
                #session.pop('saldoUsuario', None)
                cur = mysql.connection.cursor()
                cur.execute("SELECT dataHoraMovimentacao, movimentacao, tipoMovimentacao FROM movimentacaoConta WHERE user_id = %s AND dataHoraMovimentacao >= %s AND dataHoraMovimentacao <= %s AND tipoMovimentacao = %s", (session['idUsuario'], session["dataMovimentacaoInicialCache"], session["dataMovimentacaoLimiteCache"], session["tipoTransacaoCache"]))

                dataMovimentacao = []
                movimentacao = []
                tipoMovimentacao = []

                for i in cur:
                    dataMovimentacao.append(i[0])
                    movimentacao.append(i[1])
                    tipoMovimentacao.append(i[2])

                tabelaMovimentacao = pd.DataFrame(list(zip(dataMovimentacao, movimentacao, tipoMovimentacao)), columns =['Data','Movimentação', 'Tipo de Movimentação'])

                tabelaMovimentacao.to_csv(r'extrato.txt', header=True, index=False, sep='\t', mode='a')

                return render_template("tela-extrato.html", titulo="Extrato", tabelas=[tabelaMovimentacao.to_html(index=False)], titulos=tabelaMovimentacao.columns.values)

            elif not dataMovimentacaoInicial and not dataMovimentacaoLimite and tipoTransacao == "todos" and session["cacheApagado"] == True:
                cur = mysql.connection.cursor()
                cur.execute("SELECT dataHoraMovimentacao, movimentacao, tipoMovimentacao FROM movimentacaoConta WHERE user_id = %s", [session['idUsuario']])

                dataMovimentacao = []
                movimentacao = []
                tipoMovimentacao = []

                for i in cur:
                    dataMovimentacao.append(i[0])
                    movimentacao.append(i[1])
                    tipoMovimentacao.append(i[2])

                tabelaMovimentacao = pd.DataFrame(list(zip(dataMovimentacao, movimentacao, tipoMovimentacao)), columns = ['Data','Movimentação', 'Tipo de Movimentação'])

                tabelaMovimentacao.to_csv(r'extrato.txt', header=True, index=False, sep='\t', mode='a')
                flash("Extrato impresso com sucesso!")

                return render_template("tela-extrato.html", titulo="Extrato", tabelas=[tabelaMovimentacao.to_html(index=False)], titulos=tabelaMovimentacao.columns.values)

    #Se não for aberto uma pesquisa pelo usuário, abre todas as movimentações do usuario que estão no DB.
    else:
            session.pop("dataMovimentacaoInicialCache", None)
            session.pop("dataMovimentacaoLimiteCache", None)
            session.pop("tipoTransacaoCache", None)

            session.pop("cacheApagado", None)
            session["cacheApagado"] = True

            cur = mysql.connection.cursor()
            cur.execute("SELECT dataHoraMovimentacao, movimentacao, tipoMovimentacao FROM movimentacaoConta WHERE user_id = %s", [session['idUsuario']])

            dataMovimentacao = []
            movimentacao = []
            tipoMovimentacao = []

            for i in cur:
                dataMovimentacao.append(i[0])
                movimentacao.append(i[1])
                tipoMovimentacao.append(i[2])

            tabelaMovimentacao = pd.DataFrame(list(zip(dataMovimentacao, movimentacao, tipoMovimentacao)), columns = ['Data','Movimentação', 'Tipo de Movimentação'])

            return render_template("tela-extrato.html", titulo="Extrato", tabelas=[tabelaMovimentacao.to_html(index=False)], titulos=tabelaMovimentacao.columns.values)

@app.route("/meus-dados", methods=["GET", "POST"])
def meusDados():
    return render_template("meus_dados.html", titulo="Meus Dados")

@app.route("/alterar-dados", methods=["GET", "POST"])
def alterarDados():
    return render_template("alterar_dados.html", titulo="Alterar Dados")

@app.route("/encerrar-conta", methods=["GET", "POST"])
def encerrarConta():
    return

@app.route("/gerente", methods=["GET", "POST"])
def indexGerente():
    """ if session["gerenteLogado"] == False:
        return redirect (url_for("indexGerente")) """
    error = None

    if request.method == "POST":
        userDetails = request.form
        numMatriculaGerente = userDetails["numMatricula"]
        senhaGerente = userDetails["senhaLogin"]

        if not numMatriculaGerente or not senhaGerente:

            flash("Preencha todos os campos!")
            return redirect (url_for('indexGerente'))

        try:
            cur = mysql.connection.cursor()
            cur.execute("SELECT num_senha, gerente_id, gerente_nome, num_matricula, num_agencia FROM gerenteAgencia WHERE num_matricula = %s", [numMatriculaGerente])
            retornoContaGerente = cur.fetchone()
            senhaGravada = retornoContaGerente[0]
            session['idGerente'] = retornoContaGerente[1]
            session['nomeGerente'] = retornoContaGerente[2]
            session['matriculaGerente'] = retornoContaGerente[3]
            session['agenciaGerente'] = retornoContaGerente[4]
            session['funcaoAdministrativa'] = "Gerente de Agência"

        except Exception as ex:

             flash("Conta não existe no sistema! Solicite o cadastro a um Gerente Geral para continuar.")
             return render_template("login_gerente.html", tituloNavegador="Bem-vindo!")

        if senhaGerente == senhaGravada:
            session.pop('gerenteLogado', None)
            session["gerenteLogado"] = True
            return redirect (url_for('homeGerente'))
        else:
            flash("Senha incorreta!")
            return render_template("login_gerente.html", tituloNavegador="Bem-vindo!")

    return render_template("login_gerente.html", tituloNavegador="Bem-vindo!", error = error)

@app.route("/homeGerente", methods=["GET", "POST"])
def homeGerente():
    if session["gerenteLogado"] == False:
        return redirect (url_for("indexGerente"))
    return render_template("tela-home-ga.html")

@app.route("/clientes", methods=["GET", "POST"])
def clientes():
    if session["gerenteLogado"] == False:
        return redirect (url_for("indexGerente"))
        
    if request.method == "POST":
        nomeUsuario = request.form.get("nomeCliente")
    else:
        cur = mysql.connection.cursor()
        cur.execute("SELECT nome, abertura_id FROM confirmacaoAbertura where statusSolicitacao = 'Confirmada'")

        usuarioSolicitacao = []
        aberturaId = []

        for i in cur:
            usuarioSolicitacao.append(i[0])
            aberturaId.append(i[1])

        colunas = ("Cliente", "Visualizar")
        dados = list(zip(usuarioSolicitacao, aberturaId))

        return render_template("tela-clientes.html", titulo="Clientes", colunas = colunas, dados = dados)
    return render_template("tela-clientes.html", titulo="Clientes")

@app.route("/informacoes-cliente", methods=["GET", "POST"])
def infoCliente():
    idCliente = request.args.get("idCliente")
    cur = mysql.connection.cursor()

    cur.execute("SELECT user_id from confirmacaoAbertura where abertura_id = %s", ([idCliente]))
    idUsuarioRetorno = cur.fetchone()
    idUsuario = idUsuarioRetorno[0]

    cur.execute("SELECT dataHoraSolicitacao from gerenciamentoUsuarios where user_id = %s and tipoSolicitacao = 'Abertura'", ([idUsuario]))
    dataClientelaRetorno = cur.fetchone()
    session["dataClientela"] = dataClientelaRetorno[0]

    cur.execute("SELECT nome, cpf, dataAniversario, genero, endereco, contaBancaria, agenciaBancaria, saldoBancario FROM users WHERE user_id = %s", ([idUsuario]))
    dadosUsuarioCadastro = cur.fetchone()

    session["nomeUsuarioCadastro"] = dadosUsuarioCadastro[0]
    session["cpfUsuarioCadastro"] = dadosUsuarioCadastro[1]
    session["dataAniversarioCadastro"] = dadosUsuarioCadastro[2]
    session["generoCadastro"] = dadosUsuarioCadastro[3]
    session["enderecoCadastro"] = dadosUsuarioCadastro[4]
    session["contaBancariaCadastro"] = dadosUsuarioCadastro[5]
    session["agenciaBancariaCadastro"] = dadosUsuarioCadastro[6]
    session["saldoBancarioCadastro"] = dadosUsuarioCadastro[7]

    return render_template("tela-info-cliente.html", titulo="Cliente", idCliente = idCliente)

@app.route("/gerenciar", methods=["GET", "POST"])
def gerenciar():
    #Se a sessão do Usuario for Falsa, a rota deve voltar para indexHome
    if session["gerenteLogado"] == False:
        return redirect (url_for("indexGerente"))
    
    #Se o usuario clicar em Pesquisar retorna ao HTML a tabela contendo o conteúdo pesquisado.
    if request.method == "POST":
        #O type date do HTML retorna o form do usuario no formato YYYY-MM-DD, foi preciso alterar "-" por "/" e "ano" por "dia"
        dataSolicitacaoInicial = request.form.get("data-inicial")
        dataSolicitacaoInicial = dataSolicitacaoInicial[-2:] + dataSolicitacaoInicial[4:8] + dataSolicitacaoInicial[0:4]
        dataSolicitacaoInicial = dataSolicitacaoInicial.replace("-","/")
        session["dataSolicitacaoInicialCache"] = dataSolicitacaoInicial
        #O type date do HTML retorna o form do usuario no formato YYYY-MM-DD, foi preciso alterar "-" por "/" e "ano" por "dia"
        dataSolicitacaoLimite = request.form.get("data-limite")
        dataSolicitacaoLimite = dataSolicitacaoLimite[-2:] + dataSolicitacaoLimite[4:8] + dataSolicitacaoLimite[0:4]
        dataSolicitacaoLimite = dataSolicitacaoLimite.replace("-","/")
        session["dataSolicitacaoLimiteCache"] = dataSolicitacaoLimite
        #Estava retornando deposito, sem acento, acrescentei o acento pois será feito um query no DB através dessa variável
        tipoSolicitacao = request.form.get("tipo-solicitacao")
        if tipoSolicitacao == "deposito":
            tipoSolicitacao = tipoSolicitacao[0:3] + "ó" + tipoSolicitacao[4:]
            session["tipoSolicitacaoCache"] = tipoSolicitacao
        session["tipoSolicitacaoCache"] = tipoSolicitacao
        if tipoSolicitacao == "alteracoes de dados":
            tipoSolicitacao = tipoSolicitacao[0:6] + "çõ" + tipoSolicitacao[7:]
            session["tipoSolicitacaoCache"] = tipoSolicitacao
        session["tipoSolicitacaoCache"] = tipoSolicitacao
        
        app.logger.info(str(session["dataSolicitacaoInicialCache"]), str(session["dataSolicitacaoLimiteCache"]), str(session["tipoSolicitacaoCache"]))

        #Pegando as variaveis do Banco de Dados segundo os dados informados pelo Usuário x

        #Se houver dados em dataMovimentacao e não houver em tipoTransacao, mostrar a dataMovimentacao selecionada para todos os tipos de Transacao
        if dataSolicitacaoInicial and dataSolicitacaoLimite and tipoSolicitacao == "todos":
            cur = mysql.connection.cursor()
            cur.execute("SELECT dataHoraSolicitacao, tipoSolicitacao, usuarioDaSolicitacao, solicitacao_id FROM gerenciamentoUsuarios WHERE dataHoraSolicitacao >= %s AND dataHoraSolicitacao <= %s", ([dataSolicitacaoInicial], [dataSolicitacaoLimite]))

            dataSolicitacao = []
            tipoSolicitacaoBanco = []
            usuarioSolicitacao = []
            solicitacaoId = []

            for i in cur:
                dataSolicitacao.append(i[0])
                tipoSolicitacaoBanco.append(i[1])
                usuarioSolicitacao.append(i[2])
                solicitacaoId.append(i[3])

            colunas = ("Data", "Usuário", "Tipo de Solicitação", "Visualizar")
            dados = list(zip(dataSolicitacao, usuarioSolicitacao, tipoSolicitacaoBanco, solicitacaoId))

            app.logger.info(dados)

            return render_template("tela-gerenciar.html", titulo="Solicitações", colunas = colunas, dados = dados)

        #Se a dataMovimentacao e o tipoTransacao forem especificados, mostrar a dataMovimentacao e o tipo de Transacao especificado
        elif dataSolicitacaoInicial and dataSolicitacaoLimite and tipoSolicitacao != "todos":
            cur = mysql.connection.cursor()
            cur.execute("SELECT dataHoraSolicitacao, tipoSolicitacao, usuarioDaSolicitacao, solicitacao_id FROM gerenciamentoUsuarios WHERE dataHoraSolicitacao >= %s AND dataHoraSolicitacao <= %s AND tipoSolicitacao = %s", ([dataSolicitacaoInicial], [dataSolicitacaoLimite], [tipoSolicitacao]))

            dataSolicitacao = []
            tipoSolicitacaoBanco = []
            usuarioSolicitacao = []
            solicitacaoId = []

            for i in cur:
                dataSolicitacao.append(i[0])
                tipoSolicitacaoBanco.append(i[1])
                usuarioSolicitacao.append(i[2])
                solicitacaoId.append(i[3])

            colunas = ("Data", "Usuário", "Tipo de Solicitação", "Visualizar")
            dados = list(zip(dataSolicitacao, usuarioSolicitacao, tipoSolicitacaoBanco, solicitacaoId))

            return render_template("tela-gerenciar.html", titulo="Solicitações", colunas = colunas, dados = dados)

        #Se não for especificado nenhum dado para dataMovimentacao, mas ser para o tipoTransacao, mostrar todos os dados do tipoTransacao em todas as datas
        elif not dataSolicitacaoInicial and not dataSolicitacaoLimite and tipoSolicitacao != "todos":
            cur = mysql.connection.cursor()
            cur.execute("SELECT dataHoraSolicitacao, tipoSolicitacao, usuarioDaSolicitacao, solicitacao_id FROM gerenciamentoUsuarios WHERE tipoSolicitacao = %s", ([tipoSolicitacao]))

            dataSolicitacao = []
            tipoSolicitacao = []
            usuarioSolicitacao = []
            solicitacaoId = []

            for i in cur:
                dataSolicitacao.append(i[0])
                tipoSolicitacao.append(i[1])
                usuarioSolicitacao.append(i[2])
                solicitacaoId.append(i[3])

            colunas = ("Data", "Usuário", "Tipo de Solicitação", "Visualizar")
            dados = list(zip(dataSolicitacao, usuarioSolicitacao, tipoSolicitacao, solicitacaoId))

            return render_template("tela-gerenciar.html", titulo="solicitações", colunas = colunas, dados = dados)

        elif not dataSolicitacaoInicial and not dataSolicitacaoLimite and tipoSolicitacao == "todos":
            cur = mysql.connection.cursor()
            cur.execute("SELECT dataHoraSolicitacao, tipoSolicitacao, usuarioDaSolicitacao, solicitacao_id FROM gerenciamentoUsuarios")

            dataSolicitacao = []
            tipoSolicitacao = []
            usuarioSolicitacao = []
            solicitacaoId = []

            for i in cur:
                dataSolicitacao.append(i[0])
                tipoSolicitacao.append(i[1])
                usuarioSolicitacao.append(i[2])
                solicitacaoId.append(i[3])

            colunas = ("Data", "Usuário", "Tipo de Solicitação", "Visualizar")
            dados = list(zip(dataSolicitacao, usuarioSolicitacao, tipoSolicitacao, solicitacaoId))

            return render_template("tela-gerenciar.html", titulo="Solicitações", colunas = colunas, dados = dados)

    #Se não for aberto uma pesquisa pelo usuário, abre todas as movimentações do usuario que estão no DB.
    else:
            cur = mysql.connection.cursor()
            cur.execute("SELECT dataHoraSolicitacao, tipoSolicitacao, usuarioDaSolicitacao, solicitacao_id FROM gerenciamentoUsuarios")

            dataSolicitacao = []
            tipoSolicitacao = []
            usuarioSolicitacao = []
            solicitacaoId = []

            for i in cur:
                dataSolicitacao.append(i[0])
                tipoSolicitacao.append(i[1])
                usuarioSolicitacao.append(i[2])
                solicitacaoId.append(i[3])

            colunas = ("Data", "Usuário", "Tipo de Solicitação", "Visualizar")
            dados = list(zip(dataSolicitacao, usuarioSolicitacao, tipoSolicitacao, solicitacaoId))

            return render_template("tela-gerenciar.html", titulo="Solicitações", colunas = colunas, dados = dados)

@app.route("/confirmacao-deposito", methods = ["GET", "POST"])
def confirmacaoDeposito():
    solicitacaoIdCadastro = request.args.get("solicitacaoIdDeposito")
    tipoMovimentacao = "Depósito"

    cur = mysql.connection.cursor()
    cur.execute("SELECT nome, contaBancaria, agenciaBancaria, saldoAtual, valorDeposito, saldoFinal, user_id FROM confirmacaoDeposito WHERE solicitacao_id = %s", ([solicitacaoIdCadastro]))

    dadosUsuarioDeposito = cur.fetchone()
    session["nomeUsuario"] = dadosUsuarioDeposito[0]
    session["contaUsuario"] = dadosUsuarioDeposito[1]
    session["agenciaBancariaUsuario"] = dadosUsuarioDeposito[2]
    session["saldoAtualUsuario"] = dadosUsuarioDeposito[3]
    session["valorDepositoUsuario"] = dadosUsuarioDeposito[4]
    session["saldoFinalUsuario"] = dadosUsuarioDeposito[5]
    session["userIdUsuario"] = dadosUsuarioDeposito[6]

    cur.execute("SELECT saldoBancario FROM users WHERE contaBancaria = %s", [session["contaUsuario"]])
    saldoAtual = cur.fetchone()
    saldoAtual = saldoAtual[0]

    if request.method == "POST":
        if "confirmar" in request.form:
            #Para fazer UPDATES onde as duas variaveis precisam ser mudadas, basta utilizar o %s. Entretanto, no final como é uma Tupla, preciso informar o que substituir por meio de um parênteses EX:([x],[y]).   

            cur = mysql.connection.cursor()

            saldoNovo = saldoAtual + int(session["valorDepositoUsuario"])

            cur.execute("UPDATE users SET saldoBancario = %s WHERE user_id= %s", ([saldoNovo], session['userIdUsuario']))
            cur.execute("INSERT INTO movimentacaoConta (dataHoraMovimentacao, tipoMovimentacao, movimentacao, user_id) VALUES (%s, %s, %s, %s)", (session['horaSistema'], [tipoMovimentacao], session["valorDepositoUsuario"], session['userIdUsuario']))
            mysql.connection.commit()
            cur.close()
            flash("Confirmação de depósito feita com sucesso!")
        else:
            flash("Cancelamento de depósito feito com sucesso!")
        
    return render_template("tela-confirmacao-deposito.html", titulo="Solicitações", solicitacaoIdCadastro = solicitacaoIdCadastro)

@app.route("/confirmacao-abertura", methods = ["GET", "POST"])
def confirmacaoAbertura():
    solicitacaoIdAbertura = request.args.get("solicitacaoIdAbertura")

    cur = mysql.connection.cursor()
    cur.execute("SELECT nome, cpf, dataAniversario, genero, endereco, contaBancaria, agenciaBancaria, statusSolicitacao FROM confirmacaoAbertura WHERE solicitacao_id = %s", ([solicitacaoIdAbertura]))
    dadosUsuarioCadastro = cur.fetchone()
    session["nomeUsuarioCadastro"] = dadosUsuarioCadastro[0]
    session["cpfUsuarioCadastro"] = dadosUsuarioCadastro[1]
    session["dataAniversarioAbertura"] = dadosUsuarioCadastro[2]
    session["generoAbertura"] = dadosUsuarioCadastro[3]
    session["enderecoAbertura"] = dadosUsuarioCadastro[4]
    session["contaBancariaAbertura"] = dadosUsuarioCadastro[5]
    session["agenciaBancariaAbertura"] = dadosUsuarioCadastro[6]

    if request.method == "POST":
        if "confirmar" in request.form:
            statusSolicitacao = "Confirmada"

            cur = mysql.connection.cursor()
            cur.execute("UPDATE confirmacaoAbertura SET statusSolicitacao = %s WHERE contaBancaria= %s", ([statusSolicitacao], session["contaBancariaAbertura"]))
            mysql.connection.commit()
            cur.close()

            flash("Confirmação de abertura de conta feita com sucesso!")
        else:
            statusSolicitacao = "Cancelada"

            cur = mysql.connection.cursor()
            cur.execute("UPDATE confirmacaoAbertura SET statusSolicitacao = %s WHERE contaBancaria= %s", ([statusSolicitacao], session["contaBancariaAbertura"]))
            mysql.connection.commit()
            cur.close()

            flash("Cancelamento de abertura de conta feito com sucesso!")

    return render_template("tela-abertura-conta.html", titulo="Solicitações", solicitacaoIdAbertura = solicitacaoIdAbertura)

@app.route("/editar-gerentes", methods=["GET", "POST"])
def editarGerentes():
    #idGerente = request.args.get("idGerente")
    idGerenteLista = 1
    cur = mysql.connection.cursor()
    
    cur.execute("SELECT gerente_id from gerenteAgencia where gerente_id = %s", ([idGerenteLista]))
    idGerenteRetorno = cur.fetchone()
    idGerenteAgencia = idGerenteRetorno[0]

    cur.execute("SELECT gerente_nome, gerente_cpf, gerente_nasc, gerente_genero, gerente_end, num_matricula, num_agencia FROM gerenteAgencia WHERE gerente_id = %s", ([idGerenteAgencia]))
    dadosGerenteCadastro = cur.fetchone()

    session["nomeGerenteCadastro"] = dadosGerenteCadastro[0]
    session["cpfGerenteCadastro"] = dadosGerenteCadastro[1]
    session["nascGerenteCadastro"] = dadosGerenteCadastro[2]
    session["generoGerenteCadastro"] = dadosGerenteCadastro[3]
    session["endGerenteCadastro"] = dadosGerenteCadastro[4]
    session["matriculaGerenteCadastro"] = dadosGerenteCadastro[5]
    session["numAgenciaCadastro"] = dadosGerenteCadastro[6]

    if request.method == 'POST':
        if "confirmar" in request.form:

            novoNomeGerente = request.form['nomeGerenteCadastro']
            novoNumCpfGerente = request.form['cpfGerenteCadastro']
            novoNascGerente = request.form['nascGerenteCadastro']
            novoGeneroGerente = request.form['generoGerenteCadastro']
            novoEndGerente = request.form['endGerenteCadastro']
            novoNumMatriculaGerente = request.form['matriculaGerenteCadastro']
            novoNumAgenciaGerente = request.form['numAgenciaCadastro']


            cur.execute("UPDATE gerenteAgencia SET gerente_nome = %s, gerente_cpf = %s, gerente_nasc = %s, gerente_genero = %s, gerente_end = %s num_matricula = %s, num_agencia = %s WHERE gerente_id = %s", ([novoNomeGerente], [novoNumCpfGerente], [novoNascGerente], [novoGeneroGerente], [novoEndGerente], [novoNumMatriculaGerente], [novoNumAgenciaGerente], [idGerenteAgencia]))
            mysql.connection.commit()
            cur.close()
            flash("Dados atualizados com sucesso!")
            return redirect(url_for("editarGerentes"))
        else:
            flash("Dados não atualizados.")
            return redirect(url_for("editarGerentes"))
    return render_template("editar_gerente.html", titulo="Editar Gerente")

@app.route("/editar-agencia", methods=["GET", "POST"])
def editarAgencia():
    #idAgencia = request.args.get("idAgencia")
    idAgenciaLista = 1
    cur = mysql.connection.cursor()

    cur.execute("SELECT agencia_id from agencias where agencia_id = %s", ([idAgenciaLista]))
    idAgenciaRetorno = cur.fetchone()
    idAgencias = idAgenciaRetorno[0]

    cur.execute("SELECT numero_agencia, numero_clientes, nome_gerente, end_agencia FROM agencias WHERE agencia_id = %s", ([idAgencias]))
    dadosAgencia = cur.fetchone()

    session["numeroAgencia"] = dadosAgencia[0]
    session["numeroClientes"] = dadosAgencia[1]
    session["nomeGerente"] = dadosAgencia[2]
    session["enderecoAgencia"] = dadosAgencia[3]

    if request.method == 'POST':
        if "confirmar" in request.form:
            novoNumeroAgencia = request.form['numeroAgencia']
            novoNomeGerente = request.form['nomeGerente']
            novoEndAgencia = request.form['enderecoAgencia']

            cur.execute("UPDATE agencias SET numero_agencia = %s, nome_gerente = %s, end_agencia = %s WHERE agencia_id = %s", ([novoNumeroAgencia], [novoNomeGerente], [novoEndAgencia]))
            mysql.connection.commit()
            cur.close()
            flash("Dados atualizados com sucesso!")
            return redirect(url_for("editarAgencia"))
        else:
            flash("Dados não atualizados.")
            return redirect(url_for("editarAgencia"))
    return render_template("editar_agencia.html")

@app.route("/gerentes", methods=["GET", "POST"])
def gerentes():
    return render_template("gerentes.html", titulo="Gerentes")

@app.route("/informacoes-gerente", methods=["GET", "POST"])
def infoGerente():
    return render_template("info_gerente.html", titulo="Gerente") 

@app.route("/home-gerente-geral", methods=["GET", "POST"])
def homeGerenteGeral():
    return render_template("home_gg.html")

#Comando inicia automaticamente o programa, habilitando o debug sempre que algo for atualizado!
app.run(debug=True)
