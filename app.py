from flask import Flask, render_template, request, redirect, url_for, flash, session, make_response
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash, check_password_hash
import yaml
import random
import pandas as pd
from datetime import datetime
import pdfkit
from dateutil.relativedelta import *
import json

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
    with open("config.json", "w") as outfile:
        json.dump(data, outfile)
    return data

@app.route("/configuracao-banco", methods=["GET", "POST"])
def configBanco():
    if request.method == 'POST':
        userDetails = request.form
        capitalTotal = userDetails["capitalTotal"]
        taxaJurosPoupanca = userDetails["taxaPoupanca"]
        taxaJurosPoupanca = float(taxaJurosPoupanca) / 100
        taxaJurosCheque = userDetails["taxaCheque"]
        taxaJurosCheque = float(taxaJurosCheque) / 100
        dataInicializacao = dataAgora()
        
        with open ("config.json") as arquivo:
            dataJson = json.load(arquivo)
        #dataCorrente = pegar do json seria interessante, salvar no banco de dados. 

        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO configBanco (dataInicializacao, dataCorrente, capitalTotal, taxaJurosPoupanca, taxaJurosCheque) VALUES(%s, %s, %s, %s, %s)", (dataInicializacao, dataJson, capitalTotal, taxaJurosPoupanca, taxaJurosCheque))
        cur.connection.commit()
        cur.close()

        cur = mysql.connection.cursor()
        cur.execute("UPDATE gerenteGeral set GG_primeira_vez = 0")
        cur.connection.commit()
        cur.close()

        return redirect(url_for("homeGerenteGeral"))

    return render_template("configuracoes-banco.html")

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
            cur.execute("SELECT senha, user_id, contaBancaria, nome, agenciaBancaria, saldoBancario, tipoConta FROM users WHERE contaBancaria = %s", [numContaUsuario])
            #O resultado da query acima será "capturado" através de fetchone() dentro da variável senhaCriptografada. Parece que ao ser capturado o resultado vira uma lista.
            retornoContaUsuario = cur.fetchone()
            senhaCriptografada = retornoContaUsuario[0]
            session['idUsuario'] = retornoContaUsuario[1]
            session['contaUsuario'] = retornoContaUsuario[2]
            session['nomeUsuario'] = retornoContaUsuario[3]
            session['agenciaUsuario'] = retornoContaUsuario[4]
            session['saldoUsuario'] = retornoContaUsuario[5]
            session['tipoContaUsuario'] = retornoContaUsuario[6]

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
            elif statusSolicitacao == "Fechada":
                flash("Sua conta bancária foi apagada conforme requesitado!")
                return redirect (url_for('indexHome'))
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
    try:
        #Inicializando algumas variaveis importantes pro resto da função indexCadastro. A variável agenciaBancaria recebe por enquanto uma string "0001". O saldoBancario sempre começa com 0 Reais.

        # !! Talvez dê para mudar o ponto por vírgula usando replace() !!
        saldoBancario = "0.00"
        cadastro = False
        voltarLogin = False
        statusSolicitacao = "Pendente"

        cur = mysql.connection.cursor()
        cur.execute("SELECT MIN(numero_clientes) AS minimum FROM agencias")
        retornoNumeroAgencia = cur.fetchone()
        menorAgencia = retornoNumeroAgencia[0]
        app.logger.info(menorAgencia)

        cur.execute("SELECT gerente_id, numero_agencia FROM agencias where numero_clientes = %s", [menorAgencia])
        retornoAgenciaEscolhida = cur.fetchone()
        app.logger.info(retornoAgenciaEscolhida)
        gerenteEscolhido = retornoAgenciaEscolhida[0]
        agenciaEscolhida = retornoAgenciaEscolhida[1]
        agenciaEscolhida = str(agenciaEscolhida)
        app.logger.info(agenciaEscolhida)
        
        #Configurando a aquisicão das variaveis do formulario em HTML pelo request em Python (metódo POST)
        if request.method == "POST":

            userDetails = request.form
            name = userDetails["nome"]
            cpf = userDetails["cpf"]
            dataAniversario = userDetails["dataAniversario"]
            genero = userDetails["genero"]
            endereco = userDetails["endereco"]
            tipoConta = userDetails["tipoConta"]        
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

            #Aqui
            cur.execute("INSERT INTO users (agenciaBancaria, contaBancaria, saldoBancario, nome, cpf, dataAniversario, genero, endereco, senha, confirmacaoSenha, tipoConta, chequeEspecial, gerente_id) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", (agenciaEscolhida, contaBancaria, saldoBancario, name, cpf, dataAniversario, genero, endereco, senhaCriptografada, senhaCriptografada2, tipoConta, [0],gerenteEscolhido))
            
            mysql.connection.commit()

            cur.close()
            cadastro = True

            #Lógica para retornar usuário ao Login pós Cadastro e mostrar o numero da sua conta bancaria para Logar.
            if cadastro == True:
                cur = mysql.connection.cursor()
                cur.execute("SELECT MIN(numero_clientes) AS minimum FROM agencias")
                retornoNumeroAgencia = cur.fetchone()
                menorAgencia = retornoNumeroAgencia[0]
                app.logger.info(menorAgencia)

                cur.execute("SELECT numero_agencia FROM agencias where numero_clientes = %s", [menorAgencia])
                retornoAgenciaEscolhida = cur.fetchone()
                agenciaEscolhida = retornoAgenciaEscolhida[0]
                agenciaEscolhida = str(agenciaEscolhida)

                app.logger.info(agenciaEscolhida)
                
                menorAgencia = int(menorAgencia) + 1
                
                cur.execute("UPDATE agencias SET numero_clientes = %s WHERE numero_agencia = %s", ([menorAgencia], [agenciaEscolhida]))

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

                #Aqui
                cur.execute("INSERT INTO confirmacaoAbertura (nome, cpf, dataAniversario, genero, endereco, contaBancaria, agenciaBancaria, tipoConta, user_id, statusSolicitacao, solicitacao_id) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", ([name], [cpf], [dataAniversario], [genero], [endereco], [contaBancaria], [agenciaEscolhida], [tipoConta], [solicitacaoidUsuarioCadastrado], [statusSolicitacao], [solicitacaoId]))
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
    except Exception as ex:
        flash("Algo deu errado! Talvez não exista gerentes ou agências próximos de sua localidade, por favor aguarde!")
        return redirect(url_for("indexHome"))

    return render_template("cadastro.html", tituloNavegador="Novo Cliente")

#Rota home
@app.route("/deposito", methods=["GET", "POST"])
def deposito():
    if session["usuarioLogado"] == False:
        return redirect (url_for("indexHome"))

    cur = mysql.connection.cursor()
    cur.execute("SELECT saldoBancario FROM users WHERE user_id = %s", [session['idUsuario']])
    retornoSaldoAtual = cur.fetchone()
    saldoAtualUsuario = retornoSaldoAtual[0]
    session.pop('saldoUsuario', None)
    saldoFormatado = '{0:.2f}'.format(saldoAtualUsuario)
    session['saldoUsuario'] = saldoFormatado.replace('.',',')

    chequeEspecial = False

    #trazer dados do BD
    try:
        cur = mysql.connection.cursor()
        cur.execute("SELECT u.chequeEspecial, u.saldoBancario, c.dataInicial, c.valorSaque, c.valorTaxa from users u, chequeEspecial c WHERE u.user_id = c.user_id and u.user_id = %s", ([session["idUsuario"]]))
        retornoSituacaoChequeEspecial = cur.fetchone()

        situacaoChequeCliente = retornoSituacaoChequeEspecial[0]
        saldoAtualCliente = retornoSituacaoChequeEspecial[1]
        dataInicialCheque = retornoSituacaoChequeEspecial[2]

        valorMontanteNegativo = retornoSituacaoChequeEspecial[3]
        valorMontanteNegativo = float(valorMontanteNegativo)

        valorTaxaCheque = retornoSituacaoChequeEspecial[4]
        valorTaxaCheque = float(valorTaxaCheque)

    except Exception as ex:
        cur = mysql.connection.cursor()
        cur.execute("SELECT chequeEspecial from users WHERE user_id = %s", ([session["idUsuario"]]))
        retornoSituacaoChequeEspecial = cur.fetchone()
        situacaoChequeCliente = retornoSituacaoChequeEspecial[0]

    if situacaoChequeCliente == 1:
        chequeEspecial = True

        #editando a data para o timestampdiff
        dataInicialCheque = str(dataInicialCheque)
        dataInicialChequeEditado = dataInicialCheque[-4:] + dataInicialCheque[2:6] + dataInicialCheque[0:2]
        dataInicialChequeEditado = dataInicialChequeEditado.replace("/","-")

        with open("config.json", "r") as outfile:
            viagemTemporal = json.load(outfile)
        
        viagemTemporal = str(viagemTemporal)
        viagemTemporalEditado = viagemTemporal[-4:] + viagemTemporal[2:6] + viagemTemporal[0:2]
        viagemTemporalEditado = viagemTemporalEditado.replace("/","-")

        app.logger.info(dataInicialChequeEditado, viagemTemporalEditado)

        cur = mysql.connection.cursor()
        cur.execute("SELECT TIMESTAMPDIFF(day,%s,%s)", ([str(dataInicialChequeEditado)], [str(viagemTemporalEditado)]))
        retornoDiferencaDias = cur.fetchone()
        diasCobranca = retornoDiferencaDias[0]

        app.logger.info(diasCobranca)

        montanteParaPagar = valorMontanteNegativo * ((1 + valorTaxaCheque) ** diasCobranca)
        montanteParaPagar = '{0:.2f}'.format(montanteParaPagar)
        app.logger.info(montanteParaPagar)


        #Transformando a variavel para se tornar uma session do valorNegativo atualizado com juros compostos
        montanteParaPagarNegativo = float(montanteParaPagar)
        montanteParaPagarNegativo = '{0:.2f}'.format(montanteParaPagarNegativo)
        app.logger.info(montanteParaPagarNegativo)

        session.pop('valorNegativadoComprovante', None)
        session["valorNegativadoComprovante"] = montanteParaPagarNegativo 

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
            if situacaoChequeCliente == 1:

                chequeEspecial == True

                saldoAtualNegativado = float(montanteParaPagar)
                session.pop('valorNegativadoComprovante', None)
                session["valorNegativadoComprovante"] = saldoAtualNegativado
                app.logger.info(saldoAtualNegativado)

                saldoFinalConfirmacao = float(saldoAtualNegativado) + float(valorDeposito)
                saldoFinalConfirmacao = '{0:.2f}'.format(saldoFinalConfirmacao)
                app.logger.info(saldoFinalConfirmacao)
                session.pop("saldoFinalConfirmacao", None)
                session["saldoFinalConfirmacao"] = saldoFinalConfirmacao

            if situacaoChequeCliente == 0:
        
                saldoFinalConfirmacao = float(saldoAtual) + float(valorDeposito)
                session.pop("saldoFinalConfirmacao", None)
                session["saldoFinalConfirmacao"] = saldoFinalConfirmacao
                
                session.pop("horaSistema", None)
                session["horaSistema"] = dataAgora()
                session.pop("horaSistemaComprovante", None)
                session["horaSistemaComprovante"] = datetime.now().strftime("%d/%m/%Y, %H:%M:%S")

            cur = mysql.connection.cursor()

            cur.execute("UPDATE gerenciamentoUsuarios set ultimaTransacao = 0 where tipoSolicitacao = %s", ([tipoSolicitacao]))

            ultimaTransacao = 1

            cur.execute("INSERT INTO gerenciamentoUsuarios (dataHoraSolicitacao, tipoSolicitacao, usuarioDaSolicitacao, ultimaTransacao, user_id) VALUES(%s, %s, %s, %s, %s)", (session['horaSistema'], [tipoSolicitacao], session["nomeUsuario"], [ultimaTransacao], session["idUsuario"]))
            mysql.connection.commit()

            cur.execute("SELECT solicitacao_id from gerenciamentoUsuarios where ultimaTransacao = %s and tipoSolicitacao = %s", ([ultimaTransacao], [tipoSolicitacao]))
            retornoSolicitacaoId = cur.fetchone()
            solicitacaoId = retornoSolicitacaoId[0]    

            statusSolicitacao = "Pendente"
            cur.execute("INSERT INTO confirmacaoDeposito (nome, contaBancaria, agenciaBancaria, saldoAtual, valorDeposito, saldoFinal, statusSolicitacao, user_id, solicitacao_id) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)", (session["nomeUsuario"], session["contaUsuario"], session["agenciaUsuario"], [saldoAtual], [valorDeposito], [saldoFinalConfirmacao], [statusSolicitacao], session["idUsuario"], [solicitacaoId]))

            try:
                cur.execute("UPDATE chequeEspecial SET dataFinal = %s, valorNegativoAtualizado = %s, valorPago = %s WHERE user_id = %s", ([viagemTemporal], [saldoAtualNegativado], [valorDeposito], [session["idUsuario"]]))
            except Exception as ex:
                pass
            
            #Atualizando valor do BD chequeEspecial com os juros compostos em base diária

            #cur.execute("UPDATE chequeEspecial set valorNegativo = %s where user_id = %s", ([montanteParaPagarNegativo], [session["idUsuario"]]))

            cur.connection.commit()
            cur.close()

            flash("Depósito realizado. Aguarde a confirmação do depósito pelo Gerente de sua agência! Para ver seu comprovante clique ")
        else:
            if not valorDeposito:
                flash("Digite um valor para depositar")
                return redirect (url_for("deposito"))
            else:
                flash("Apenas depósitos positivos e acima de R$ 0,00 são permitidos!")
                return redirect (url_for("deposito"))

        #session.pop remove os dados de 'saldoUsuario'. Em seguida pedi para que o saldo final sofresse uma formatação e ficasse com duas casas após a vírgula. depois renovei o session 'saldoUsuario' para pegar o saldo formatado. Precisei excluir e pegar novamente para atualizar o cache.
        session.pop('saldoUsuario', None)
        saldoFormatado = '{0:.2f}'.format(saldoAtual)
        session['saldoUsuario'] = saldoFormatado.replace('.',',')
        return redirect (url_for('deposito'))

    return render_template("tela-deposito.html", titulo="Depósito", error = error, chequeEspecial = chequeEspecial)

#Rota para página saque.
@app.route("/saque", methods=["GET", "POST"])
def saque():
    if session["usuarioLogado"] == False:
        return redirect (url_for("indexHome"))

    cur = mysql.connection.cursor()
    cur.execute("SELECT saldoBancario FROM users WHERE user_id = %s", [session['idUsuario']])
    retornoSaldoAtual = cur.fetchone()
    saldoAtualUsuario = retornoSaldoAtual[0]
    session.pop('saldoUsuario', None)
    saldoFormatado = '{0:.2f}'.format(saldoAtualUsuario)
    session['saldoUsuario'] = saldoFormatado.replace('.',',')

    chequeEspecial = False

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
        saldoParcial = float(saldoParcial)
        session["saldoUsuarioAntes"] = saldoParcial
        session.pop('valorNegativadoComprovante', None)
        session["valorNegativadoComprovante"] = saldoParcial


        cur.execute("SELECT capitalTotal FROM configBanco")
        retornoCapitalTotal = cur.fetchone()
        capitalTotalParcial = retornoCapitalTotal[0]
        capitalTotalParcial = float(capitalTotalParcial)

        #Onde antes tinha int troquei pra float para que o depósito e saque de moedas seja permitido.
        if valorSaque and float(valorSaque) > 0 and float(valorSaque) <= float(capitalTotalParcial):

            saldoFinal = float(saldoParcial) - float(valorSaque)
            session.pop("saldoFinalConfirmacao", None)
            session["saldoFinalConfirmacao"] = saldoFinal

            capitalTotalNovo = float(capitalTotalParcial) - float(valorSaque)
            app.logger.info(float(capitalTotalNovo))

            session.pop("horaSistema", None)
            session["horaSistema"] = dataAgora()
            session.pop("horaSistemaComprovante", None)
            session["horaSistemaComprovante"] = datetime.now().strftime("%d/%m/%Y, %H:%M:%S")

            if saldoFinal < 0:
                chequeEspecial = 1
                montante = saldoFinal

                cur = mysql.connection.cursor()

                cur.execute("SELECT taxaJurosCheque from configBanco")
                retornoTaxaJurosCheque = cur.fetchone()
                taxaJurosCheque = retornoTaxaJurosCheque[0]
                taxaJurosCheque = float(taxaJurosCheque)

                cur.execute("SELECT chequeEspecial FROM users WHERE user_id = %s", ([session['idUsuario']]))
                retornoSituacaoChequeEspecial = cur.fetchone()
                situacaoChequeCliente = retornoSituacaoChequeEspecial[0]

                if situacaoChequeCliente == 0:
                    cur = mysql.connection.cursor()
                    cur.execute("INSERT INTO chequeEspecial (valorSaque, dataInicial, valorTaxa, user_id) values(%s, %s, %s, %s)", ([montante], session["horaSistema"], [taxaJurosCheque], session['idUsuario']))
                    cur.execute("UPDATE users SET chequeEspecial = '1' WHERE user_id = %s", ([session['idUsuario']]))
                    cur.connection.commit()

                else:
                    cur = mysql.connection.cursor()
                    cur.execute("UPDATE chequeEspecial SET valorSaque = %s, valorTaxa = %s WHERE user_id = %s", ([montante], [taxaJurosCheque], [session['idUsuario']]))
                    cur.connection.commit()

                flash("Atenção! Você está agora em cheque especial. Seu próximo depósito irá ser automaticamente debitado do valor sacado acrescido com juros compostos em base diária.")

            cur.execute("UPDATE users SET saldoBancario = %s WHERE user_id= %s", ([saldoFinal], session['idUsuario']))

            cur.execute("UPDATE configBanco SET capitalTotal = %s", ([float(capitalTotalNovo)]))

            cur.execute("INSERT INTO movimentacaoConta (dataHoraMovimentacao, tipoMovimentacao, movimentacao, user_id) VALUES (%s, %s, %s, %s)", (session['horaSistema'], [tipoMovimentacao], [valorSaque], session['idUsuario']))
            mysql.connection.commit()
            cur.close()
            flash("Saque realizado com sucesso! Para ver seu comprovante clique ")
        else:
            if valorSaque and float(valorSaque) <= 0:
                flash('Apenas saques acima de R$ 0,00 são permitidos!')
                return redirect(url_for('saque'))
            if not valorSaque:
                flash('Preencha o campo VALOR para realizar o saque!')
                return redirect(url_for('saque'))
            if float(valorSaque) > float(capitalTotalParcial):
                flash("Operação inválida.")
                return redirect(url_for('saque'))

        session.pop('saldoUsuario', None)
        saldoFormatado = '{0:.2f}'.format(saldoFinal)
        session['saldoUsuario'] = saldoFormatado.replace('.',',')
        return redirect (url_for('saque'))

    return render_template("tela-saque.html", titulo="Saque", error = error, chequeEspecial = chequeEspecial)

@app.route("/comprovante", methods=["GET", "POST"])
def comprovante():

    chequeEspecial = False

    cur = mysql.connection.cursor()
    cur.execute("SELECT chequeEspecial FROM users WHERE user_id = %s", ([session['idUsuario']]))
    retornoSituacaoChequeEspecial = cur.fetchone()
    situacaoChequeCliente = retornoSituacaoChequeEspecial[0]
    if situacaoChequeCliente == 1:
        chequeEspecial = True

    if request.method == 'POST':
        path_wkhtmltopdf = r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe'
        config = pdfkit.configuration(wkhtmltopdf=path_wkhtmltopdf)
        html = render_template(
            "comprovantePDF.html", chequeEspecial = chequeEspecial)
        pdf = pdfkit.from_string(html, False, configuration = config)
        response = make_response(pdf)
        response.headers["Content-Type"] = "application/pdf"
        response.headers["Content-Disposition"] = "inline; filename=output.pdf"
        return response  
    return render_template("tela-comprovante.html", titulo="Comprovante", chequeEspecial = chequeEspecial)

@app.route("/comprovante-transferencia", methods=["GET", "POST"])
def comprovanteTransferencia():
    if request.method == 'POST':
        path_wkhtmltopdf = r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe'
        config = pdfkit.configuration(wkhtmltopdf=path_wkhtmltopdf)
        html = render_template(
            "comprovanteTransferenciaPDF.html")
        pdf = pdfkit.from_string(html, False, configuration = config, options={"enable-local-file-access": ""})
        response = make_response(pdf)
        response.headers["Content-Type"] = "application/pdf"
        response.headers["Content-Disposition"] = "inline; filename=output2.pdf"  
        return response
    return render_template("tela-comprovante-transferencia.html", titulo="Comprovante")

@app.route("/comprovante-extrato", methods=["GET", "POST"])
def comprovanteExtrato():
    dataMovimentacao = request.args.getlist("dataMovimentacao", None)
    movimentacao = request.args.getlist("movimentacao", None)
    tipoMovimentacao = request.args.getlist("tipoMovimentacao", None)

    tipoMovimentacaoTexto = "EXTRATO"
    session["tipoSolicitacao"] = tipoMovimentacaoTexto

    session.pop("horaSistemaComprovante", None)
    session["horaSistemaComprovante"] = datetime.now().strftime("%d/%m/%Y, %H:%M:%S")

    tabelaMovimentacao = pd.DataFrame(list(zip(dataMovimentacao, movimentacao, tipoMovimentacao)), columns = ['Data','Movimentacao', 'Tipo de Movimentacao'])
    
    if request.method == 'POST':
        path_wkhtmltopdf = r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe'
        config = pdfkit.configuration(wkhtmltopdf=path_wkhtmltopdf)
        html = render_template(
            "comprovante-extrato-pdf.html", tabelas=[tabelaMovimentacao.to_html(index=False)], titulos=tabelaMovimentacao.columns.values)
        pdf = pdfkit.from_string(html, False, configuration = config, options={"enable-local-file-access": ""})
        response = make_response(pdf)
        response.headers["Content-Type"] = "application/pdf"
        response.headers["Content-Disposition"] = "inline; filename=output2.pdf"  
        return response
    return render_template("comprovante-extrato.html", titulo="Comprovante", tabelas=[tabelaMovimentacao.to_html(index=False)], titulos=tabelaMovimentacao.columns.values)

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
    cur = mysql.connection.cursor()
    cur.execute("SELECT saldoBancario FROM users WHERE user_id = %s", [session['idUsuario']])
    retornoSaldoAtual = cur.fetchone()
    saldoAtualUsuario = retornoSaldoAtual[0]
    session.pop('saldoUsuario', None)
    saldoFormatado = '{0:.2f}'.format(saldoAtualUsuario)
    session['saldoUsuario'] = saldoFormatado.replace('.',',')
    return render_template("tela-home.html")

#Rotas Transferencia, Extrato, Configurações inicializadas. Mas ainda sem função.
@app.route("/transferencia", methods=["GET", "POST"])
def transferencia():

    if session["usuarioLogado"] == False:
        return redirect (url_for("indexHome"))

    cur = mysql.connection.cursor()
    cur.execute("SELECT saldoBancario FROM users WHERE contaBancaria = %s", [session['contaUsuario']])
    novoSaldoAtual = cur.fetchone()
    saldoAtualEnvio = novoSaldoAtual[0]

    #session.pop remove os dados de 'saldoUsuario'. Em seguida pedi para que o saldo final sofresse uma formatação e ficasse com duas casas após a vírgula. depois renovei o session 'saldoUsuario' para pegar o saldo formatado. Precisei excluir e pegar novamente para atualizar o cache.
    session.pop('saldoUsuario', None)
    saldoFormatado = '{0:.2f}'.format(saldoAtualEnvio)
    session['saldoUsuario'] = saldoFormatado.replace('.',',')

    if request.method == "POST":

        userDetails = request.form

        valorTransferencia = userDetails["valorTransferencia"]
        session["valorTransferencia"] = valorTransferencia

        numeroContaTransferencia = userDetails["numeroConta"]
        session["numeroContaTransferencia"] = numeroContaTransferencia

        numeroAgenciaTransferencia = userDetails["numeroAgencia"]
        session["numeroAgenciaTransferencia"] = numeroAgenciaTransferencia

        tipoSolicitacaoEnviada = "Transferência enviada para a conta: " + str(session["numeroContaTransferencia"])   
        tipoSolicitacaoRecebida = "Transferência recebida da conta: " + str(session["contaUsuario"]) 

        app.logger.info(tipoSolicitacaoEnviada)
        app.logger.info(tipoSolicitacaoRecebida)

        session["tipoSolicitacaoEnviada"] = tipoSolicitacaoEnviada
        session["tipoSolicitacaoRecebida"] = tipoSolicitacaoRecebida

        if not valorTransferencia or not numeroAgenciaTransferencia or not numeroContaTransferencia:
            flash("Digite um valor para transferência!")
            return redirect (url_for("transferencia"))
        elif not numeroAgenciaTransferencia or not numeroContaTransferencia:
            flash("Digite uma conta e agência para transferir")
            return redirect (url_for("transferencia"))
        elif not valorTransferencia:
            flash("Preencha todos os campos!")
            return redirect (url_for("transferencia"))

        #verificando se a conta e a agencia existem no BD
        try:
            cur = mysql.connection.cursor()
            cur.execute("SELECT contaBancaria, agenciaBancaria FROM confirmacaoAbertura WHERE contaBancaria = %s and agenciaBancaria = %s", (session['contaUsuario'], session["numeroAgenciaTransferencia"]))
            retornoContaAgenciaExistem = cur.fetchone()
            contaExiste = retornoContaAgenciaExistem[0]
            agenciaExiste = retornoContaAgenciaExistem[1]

            
            if not contaExiste:
                flash("Conta bancária com esse número não existe no sistema, por favor verifique e tente novamente!")
                return redirect(url_for("transferencia"))
            elif contaExiste:
                if not agenciaExiste:
                    flash("Agência bancária não existe no sistema, por favor verifique e tente novamente!")
                    return redirect(url_for("transferencia"))
            else:
                pass

        except Exception as ex:
            flash("Conta bancária ou agência com esse número não existem no sistema, por favor verifique e tente novamente!")
            return redirect(url_for("transferencia"))

        cur = mysql.connection.cursor()
        cur.execute("SELECT saldoBancario FROM users WHERE contaBancaria = %s", [session['contaUsuario']])
        saldoAtualEnvio = cur.fetchone()
        saldoAtualEnvio = saldoAtualEnvio[0]
        session["saldoUsuarioAntesEnvio"] = saldoAtualEnvio

        try:
            cur.execute("SELECT saldoBancario, user_id FROM users WHERE contaBancaria = %s", [session['numeroContaTransferencia']])
            retornoDadosContaRecebido = cur.fetchone()
            saldoAtualRecebido = retornoDadosContaRecebido[0]
            session["saldoUsuarioAntesRecebido"] = saldoAtualRecebido
            idUsuarioRecebido = retornoDadosContaRecebido[1]
            session["idUsuarioRecebido"] = idUsuarioRecebido
        except Exception as ex:
            flash("Conta bancária com esse número não existe no sistema, por favor verifique e tente novamente!")
            return redirect(url_for("transferencia"))

        try:
            if valorTransferencia and float(valorTransferencia) > 0:
                #Atualizacao da hora do sistema
                session.pop("horaSistema", None)
                session["horaSistema"] = dataAgora()
                session.pop("horaSistemaComprovante", None)
                session["horaSistemaComprovante"] = datetime.now().strftime("%d/%m/%Y, %H:%M:%S")

                #Atualização valores de quem ENVIOU 
                saldoFinalEnvio = float(saldoAtualEnvio) - float(valorTransferencia)
                session["saldoFinalEnvio"] = saldoFinalEnvio

                cur.execute("UPDATE users SET saldoBancario = %s WHERE user_id= %s", ([saldoFinalEnvio], session['idUsuario']))
                cur.execute("INSERT INTO movimentacaoConta (dataHoraMovimentacao, tipoMovimentacao, movimentacao, user_id) VALUES (%s, %s, %s, %s)", (session['horaSistema'], [tipoSolicitacaoEnviada], [valorTransferencia], session['idUsuario']))
                mysql.connection.commit()
                cur.close()

                #Atualização valores de quem RECEBEU
                saldoFinalRecebido = float(saldoAtualRecebido) + float(valorTransferencia)
                session["saldoFinalRecebido"] = saldoFinalRecebido
                
                cur = mysql.connection.cursor()
                cur.execute("UPDATE users SET saldoBancario = %s WHERE user_id= %s", ([saldoFinalRecebido], session['idUsuarioRecebido']))
                cur.execute("INSERT INTO movimentacaoConta (dataHoraMovimentacao, tipoMovimentacao, movimentacao, user_id) VALUES (%s, %s, %s, %s)", (session['horaSistema'], [tipoSolicitacaoRecebida], [valorTransferencia], session['idUsuarioRecebido']))
                mysql.connection.commit()
                cur.close()

                flash("Transferência realizada com sucesso! Para ver seu comprovante clique ")
                return redirect (url_for("transferencia"))
            elif valorTransferencia and float(valorTransferencia) <= 0:
                flash("Apenas transferências positivas e acima de R$ 0,00 são permitidas!")
                return redirect (url_for("transferencia"))
        except Exception as ex:
                flash("Preencha todos os campos!")
                return redirect (url_for("transferencia"))

        cur = mysql.connection.cursor()
        cur.execute("SELECT saldoBancario FROM users WHERE contaBancaria = %s", [session['contaUsuario']])
        novoSaldoAtual = cur.fetchone()
        saldoAtualEnvio = novoSaldoAtual[0]

        #session.pop remove os dados de 'saldoUsuario'. Em seguida pedi para que o saldo final sofresse uma formatação e ficasse com duas casas após a vírgula. depois renovei o session 'saldoUsuario' para pegar o saldo formatado. Precisei excluir e pegar novamente para atualizar o cache.
        session.pop('saldoUsuario', None)
        saldoFormatado = '{0:.2f}'.format(saldoAtualEnvio)
        session['saldoUsuario'] = saldoFormatado.replace('.',',')
        return redirect (url_for('transferencia'))
    return render_template("transferencia.html", titulo="Transferência")

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

            return redirect(url_for("comprovanteExtrato", dataMovimentacao = dataMovimentacao, movimentacao = movimentacao, tipoMovimentacao = tipoMovimentacao))

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

#Teoricamente funcionaria, mas não se pode apagar uma tabela com chave estrangeira!
@app.route("/meus-dados", methods=["GET", "POST"])
def meusDados():

    cur = mysql.connection.cursor()
    cur.execute("SELECT nome, cpf, dataAniversario, genero, endereco, contaBancaria, agenciaBancaria, saldoBancario FROM users WHERE user_id = %s", str(session["idUsuario"]))
    dadosUsuario = cur.fetchone()
    session["nomeUsuario"] = dadosUsuario[0]
    session["cpfUsuario"] = dadosUsuario[1]
    session["dataAniversario"] = dadosUsuario[2]
    session["generoUsuario"] = dadosUsuario[3]
    session["enderecoUsuario"] = dadosUsuario[4]
    session["contaBancariaUsuario"] = dadosUsuario[5]
    session["agenciaBancariaUsuario"] = dadosUsuario[6]
    session["saldoBancarioUsuario"] = dadosUsuario[7]

    if request.method == "POST":
        if "encerrarConta" in request.form:
            if session["saldoBancarioUsuario"] > 0 or session["saldoBancarioUsuario"] < 0:
                flash("Antes de pedir uma solicitação de fechamento de conta, por favor deixe sua conta bancária zerada.\n Se houver saldo faça um saque ou transferência. Se houver saldo negativo faça um depósito.")
                return redirect(url_for("meusDados"))
            else:
                tipoSolicitacao = "Fechamento"
                solicitacaoEncerramento = "Pendente"

                session.pop("horaSistema", None)
                session["horaSistema"] = dataAgora()

                cur = mysql.connection.cursor()

                cur.execute("UPDATE gerenciamentoUsuarios set ultimaTransacao = 0 where tipoSolicitacao = %s", ([tipoSolicitacao]))

                ultimaTransacao = 1

                cur.execute("INSERT INTO gerenciamentoUsuarios (dataHoraSolicitacao, tipoSolicitacao, usuarioDaSolicitacao, ultimaTransacao, user_id) VALUES(%s, %s, %s, %s, %s)", (session['horaSistema'], [tipoSolicitacao], session["nomeUsuario"], [ultimaTransacao], session["idUsuario"]))
                mysql.connection.commit()

                cur.execute("SELECT solicitacao_id from gerenciamentoUsuarios where ultimaTransacao = %s and tipoSolicitacao = %s", ([ultimaTransacao], [tipoSolicitacao]))
                retornoFechamentoId = cur.fetchone()
                fechamentoId = retornoFechamentoId[0]

                cur.execute("SELECT nome, cpf, dataAniversario, genero, endereco, tipoConta, contaBancaria, agenciaBancaria, saldoBancario FROM users WHERE user_id = %s", str(session["idUsuario"]))
                dadosUsuario = cur.fetchone()
                app.logger.info(dadosUsuario)
                session["nomeUsuario"] = dadosUsuario[0]
                session["cpfUsuario"] = dadosUsuario[1]
                session["dataAniversario"] = dadosUsuario[2]
                session["generoUsuario"] = dadosUsuario[3]
                session["enderecoUsuario"] = dadosUsuario[4]
                session["tipoContaUsuario"] = dadosUsuario[5]
                session["contaBancariaUsuario"] = dadosUsuario[6]
                session["agenciaBancariaUsuario"] = dadosUsuario[7]
                session["saldoBancarioUsuario"] = dadosUsuario[8] 

                cur.execute("INSERT INTO confirmacaoFechamento (nome, cpf, dataAniversario, genero, endereco, tipoConta, contaBancaria, agenciaBancaria, user_id, statusSolicitacao, solicitacao_id) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", (session["nomeUsuario"], session["cpfUsuario"], session["dataAniversario"], session["generoUsuario"], session["enderecoUsuario"], session["tipoContaUsuario"], session["contaBancariaUsuario"], session["agenciaBancariaUsuario"], session["idUsuario"], [solicitacaoEncerramento], [fechamentoId]))
                mysql.connection.commit()
                cur.close()

                flash("Solicitação de fechamento de conta feita com sucesso. Em breve sua solicitação será avaliada por um de nossos gerentes, por favor aguarde!")
                return redirect(url_for("meusDados"))
        else:

            cur = mysql.connection.cursor()
            cur.execute("SELECT nome, cpf, dataAniversario, genero, endereco, contaBancaria, agenciaBancaria, saldoBancario FROM users WHERE user_id = %s", str(session["idUsuario"]))
            dadosUsuario = cur.fetchone()
            session["nomeUsuario"] = dadosUsuario[0]
            session["cpfUsuario"] = dadosUsuario[1]
            session["dataAniversario"] = dadosUsuario[2]
            session["generoUsuario"] = dadosUsuario[3]
            session["enderecoUsuario"] = dadosUsuario[4]
            session["contaBancariaUsuario"] = dadosUsuario[5]
            session["agenciaBancariaUsuario"] = dadosUsuario[6]
            session["saldoBancarioUsuario"] = dadosUsuario[7]
            app.logger.info(dadosUsuario)
            return redirect(url_for("meusDados"))
    return render_template("meus_dados.html", titulo="Meus Dados")

@app.route("/alterar-dados", methods = ["GET", "POST"])
def alterarDados():

     if request.method == "POST":
        if "confirmar" in request.form:
            
            userDetails = request.form
            novoNome = userDetails["nome"]
            novoCpf = userDetails["cpf"]
            novoDataAniversario = userDetails["dataAniversario"]
            novoGenero = userDetails["genero"]
            novoEndereco = userDetails["endereco"]        
            novoSenha = userDetails["senhaUsuario"]
            novoConfirmacaoSenha = userDetails["retornoSenha"]  
            novoSenhaCriptografada = generate_password_hash(novoSenha) 
            novoSenhaCriptografada2 = None
            tipoSolicitacao = "Alteração de Dados"
            statusSolicitacao = "Pendente"
            if novoSenha == novoConfirmacaoSenha:
                novoSenhaCriptografada2 = novoSenhaCriptografada
                flash("Uma solicitação de alteração de dados foi enviada ao seu gerente.")
            else:
                flash("As senhas precisam ser iguais!")
                return redirect(url_for ("alterarDados"))

            cur = mysql.connection.cursor()

            session.pop("horaSistema", None)
            session["horaSistema"] = dataAgora()

            cur.execute("UPDATE gerenciamentoUsuarios set ultimaTransacao = 0 where tipoSolicitacao = %s", ([tipoSolicitacao]))

            ultimaTransacao = 1

            cur.execute("INSERT INTO gerenciamentoUsuarios (dataHoraSolicitacao, tipoSolicitacao, usuarioDaSolicitacao, ultimaTransacao, user_id) VALUES(%s, %s, %s, %s, %s)", (session['horaSistema'], [tipoSolicitacao], session["nomeUsuario"], [ultimaTransacao], session["idUsuario"]))
            mysql.connection.commit()

            cur.execute("SELECT solicitacao_id from gerenciamentoUsuarios where ultimaTransacao = %s and tipoSolicitacao = %s", ([ultimaTransacao], [tipoSolicitacao]))
            retornoAlteracaoId = cur.fetchone()
            alteracaoId = retornoAlteracaoId[0] 

            cur.execute("INSERT INTO confirmacaoAlteracao (nome, cpf, dataAniversario, genero, endereco, senha, confirmacaoSenha, statusSolicitacao, user_id, solicitacao_id) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", (novoNome, novoCpf, novoDataAniversario, novoGenero, novoEndereco, novoSenhaCriptografada, novoSenhaCriptografada2, statusSolicitacao, session["idUsuario"], alteracaoId))
            mysql.connection.commit()
            cur.close()

        return render_template("alterar_dados.html", titulo = "Alterar Dados")

@app.route("/alterar_dados_cliente", methods = ["GET", "POST"])
def alterarDadosCliente():

    cur = mysql.connection.cursor()
    cur.execute("SELECT numero_agencia from agencias")

    listaAgenciasDisponiveis = []

    for i in cur:
        listaAgenciasDisponiveis.append(i[0])

    if request.method == "POST":
        if "confirmar" in request.form:
            
            userDetails = request.form
            retornoCpfUsuario = userDetails["cpf"]

            cur = mysql.connection.cursor()
            cur.execute("SELECT user_id FROM users WHERE cpf = %s", ([retornoCpfUsuario]))
            retornoUserID = cur.fetchone()

            cur.execute("SELECT tipoConta, nome, cpf, dataAniversario, genero, endereco, contaBancaria, agenciaBancaria FROM users WHERE user_id = %s", ([retornoUserID]))
            dadosUsuarioFechamento = cur.fetchone()

            session["tipoContaUsuario"] = dadosUsuarioFechamento[0]
            session["nomeUsuarioCadastro"] = dadosUsuarioFechamento[1]
            session["cpfUsuarioCadastro"] = dadosUsuarioFechamento[2]
            session["dataAniversarioCadastro"] = dadosUsuarioFechamento[3]
            session["generoCadastro"] = dadosUsuarioFechamento[4]
            session["enderecoCadastro"] = dadosUsuarioFechamento[5]
            session["contaBancariaCadastro"] = dadosUsuarioFechamento[6]
            session["agenciaBancariaCadastro"] = dadosUsuarioFechamento[7]


            '''cur = mysql.connection.cursor()
            cur.execute("SELECT user_id FROM users WHERE")
            retornoUserID = cur.fetchone()
            userID = retornoUserID'''

            userDetails = request.form
            novoNome = userDetails["nome"]
            novoCpf = userDetails["cpf"]
            novoDataAniversario = userDetails["dataAniversario"]
            novoGenero = userDetails["genero"]
            novoEndereco = userDetails["endereco"]
            novaAgencia = userDetails["numeroAgencia"]
            novaConta = userDetails["numeroContaUsuario"]
            novoTipoConta = userDetails["tipoContaUsuario"]

            cur.execute("SELECT gerente_id FROM agencias WHERE numero_agencia = %s", ([novaAgencia]))
            retornoGerenteId = cur.fetchone()
            retornoGerenteId = retornoGerenteId[0]


            cur.execute("UPDATE users SET nome = %s, cpf = %s, dataAniversario = %s, genero = %s, endereco = %s, agenciaBancaria = %s, contaBancaria = %s, tipoConta = %s, gerente_id = %s WHERE user_id= %s", (novoNome, novoCpf, novoDataAniversario, novoGenero, novoEndereco, novaAgencia, novaConta, novoTipoConta, retornoGerenteId, retornoUserID))
            mysql.connection.commit()
            cur.close()

            flash("Os dados do cliente foram alterados.")
            return redirect (url_for('alterarDadosCliente'))

        else:
            pass

    return render_template("alterar_dados_cliente.html", listaAgenciasDisponiveis = listaAgenciasDisponiveis)

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
            if len(numMatriculaGerente) == 5:
                cur = mysql.connection.cursor()
                cur.execute("SELECT num_senha, gerente_id, gerente_nome, num_matricula, num_agencia FROM gerenteAgencia WHERE num_matricula = %s", [numMatriculaGerente])
                retornoContaGerente = cur.fetchone()
                app.logger.info(retornoContaGerente)
                senhaGravada = retornoContaGerente[0]
                session['idGerente'] = retornoContaGerente[1]
                session['gerente_nome'] = retornoContaGerente[2]
                session['num_matricula'] = retornoContaGerente[3]
                session['num_agencia'] = retornoContaGerente[4]
                session['funcaoAdministrativa'] = "Gerente de Agência"

            else:
                cur = mysql.connection.cursor()
                cur.execute("SELECT GG_num_senha, GG_id, GG_nome, GG_num_matricula, GG_primeira_vez FROM gerenteGeral WHERE GG_num_matricula = %s", [numMatriculaGerente])

                retornoContaGerenteGeral = cur.fetchone()
                app.logger.info(retornoContaGerenteGeral)

                senhaGravada = retornoContaGerenteGeral[0]
                session['idGerente'] = retornoContaGerenteGeral[1]
                session['nomeGerente'] = retornoContaGerenteGeral[2]
                session['matriculaGerente'] = retornoContaGerenteGeral[3]
                session['primeiravezGerente'] = retornoContaGerenteGeral[4]
                session['funcaoAdministrativa'] = "Gerente Geral"

        except Exception as ex:

             flash("Conta não existe no sistema! Solicite o cadastro a um Gerente Geral para continuar.")
             return render_template("login_gerente.html", tituloNavegador="Bem-vindo!")

        if session['funcaoAdministrativa'] == "Gerente de Agência" and senhaGerente == senhaGravada:
            session.pop('gerenteLogado', None)
            session["gerenteLogado"] = True
            return redirect (url_for('homeGerente'))
           

        elif session['funcaoAdministrativa'] == "Gerente Geral" and senhaGerente == senhaGravada:
            session.pop('gerenteLogado', None)
            session["gerenteLogado"] = True
            if session['primeiravezGerente'] == 1:
                return redirect(url_for("configBanco"))
            else:
                return redirect (url_for('homeGerenteGeral'))
        
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
        cur = mysql.connection.cursor()
        if session['funcaoAdministrativa'] == "Gerente de Agência":
            cur.execute("SELECT c.nome, c.abertura_id FROM confirmacaoAbertura c, users u where u.user_id = c.user_id and c.nome = %s and c.statusSolicitacao = 'Confirmada' and u.gerente_id = %s", ([nomeUsuario], session["idGerente"]))
        else:
            cur.execute("SELECT nome, abertura_id FROM confirmacaoAbertura where statusSolicitacao = 'Confirmada' and nome = %s", ([nomeUsuario]))
        

        usuarioSolicitacao = []
        aberturaId = []

        for i in cur:
            usuarioSolicitacao.append(i[0])
            aberturaId.append(i[1])

        app.logger.info(usuarioSolicitacao, aberturaId)

        colunas = ("Cliente", "Visualizar")
        dados = list(zip(usuarioSolicitacao, aberturaId))

        return render_template("tela-clientes.html", titulo="Clientes", colunas = colunas, dados = dados)
    else:
        cur = mysql.connection.cursor()
        if session['funcaoAdministrativa'] == "Gerente de Agência":
            cur.execute("SELECT c.nome, c.abertura_id FROM confirmacaoAbertura c, users u where u.user_id = c.user_id and c.statusSolicitacao = 'Confirmada' and u.gerente_id = %s", ([session["idGerente"]]))
        else:
            cur.execute("SELECT nome, abertura_id FROM confirmacaoAbertura where statusSolicitacao = 'Confirmada'")

        usuarioSolicitacao = []
        aberturaId = []

        for i in cur:
            usuarioSolicitacao.append(i[0])
            aberturaId.append(i[1])

        app.logger.info(aberturaId)

        colunas = ("Cliente", "Visualizar")
        dados = list(zip(usuarioSolicitacao, aberturaId))

        return render_template("tela-clientes.html", titulo="Clientes", colunas = colunas, dados = dados)

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

    cur.execute("SELECT tipoConta, nome, cpf, dataAniversario, genero, endereco, contaBancaria, agenciaBancaria, saldoBancario FROM users WHERE user_id = %s", ([idUsuario]))
    dadosUsuarioFechamento = cur.fetchone()

    session["tipoContaUsuario"] = dadosUsuarioFechamento[0]
    session["nomeUsuarioCadastro"] = dadosUsuarioFechamento[1]
    session["cpfUsuarioCadastro"] = dadosUsuarioFechamento[2]
    session["dataAniversarioCadastro"] = dadosUsuarioFechamento[3]
    session["generoCadastro"] = dadosUsuarioFechamento[4]
    session["enderecoCadastro"] = dadosUsuarioFechamento[5]
    session["contaBancariaCadastro"] = dadosUsuarioFechamento[6]
    session["agenciaBancariaCadastro"] = dadosUsuarioFechamento[7]
    session["saldoBancarioCadastro"] = dadosUsuarioFechamento[8]

    if request.method == "POST":
        
        '''if "confirmar" in request.form:

            cur.execute("SELECT user_id FROM users")
            retornoUserID = cur.fetchone()
            userID = retornoUserID

            userDetails = request.form
            novoNome = userDetails["nome"]
            novoCpf = userDetails["cpf"]
            novoDataAniversario = userDetails["dataAniversario"]
            novoGenero = userDetails["genero"]
            novoEndereco = userDetails["endereco"]

            flash("Os dados do cliente foram alterados.")
        else:
            flash("Os dados do cliente não foram alterados.")

            cur = mysql.connection.cursor()

            cur.execute("UPDATE users SET nome = %s, cpf = %s, dataAniversario = %s, genero = %s, endereco = %s WHERE user_id= %s", novoNome, novoCpf, novoDataAniversario, novoGenero, novoEndereco, userID)
            mysql.connection.commit()
            cur.close()'''

        return redirect (url_for('alterarDadosCliente', idCliente = idCliente))

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
        """ if tipoSolicitacao == "deposito":
            tipoSolicitacao = tipoSolicitacao[0:3] + "ó" + tipoSolicitacao[4:]
            session["tipoSolicitacaoCache"] = tipoSolicitacao
        session["tipoSolicitacaoCache"] = tipoSolicitacao """

        """ if tipoSolicitacao == "alteracao de dados":
            tipoSolicitacao = tipoSolicitacao[0:6] + "çã" + tipoSolicitacao[8:]
            session["tipoSolicitacaoCache"] = tipoSolicitacao
        session["tipoSolicitacaoCache"] = tipoSolicitacao """
        
        app.logger.info(str(session["dataSolicitacaoInicialCache"]), str(session["dataSolicitacaoLimiteCache"]), str(session["tipoSolicitacaoCache"]))

        #Pegando as variaveis do Banco de Dados segundo os dados informados pelo Usuário x

        #Se houver dados em dataMovimentacao e não houver em tipoTransacao, mostrar a dataMovimentacao selecionada para todos os tipos de Transacao
        if dataSolicitacaoInicial and dataSolicitacaoLimite and tipoSolicitacao == "todos":
            cur = mysql.connection.cursor()
            if session['funcaoAdministrativa'] == "Gerente de Agência":
                cur.execute("SELECT g.dataHoraSolicitacao, g.tipoSolicitacao, g.usuarioDaSolicitacao, g.solicitacao_id FROM gerenciamentoUsuarios g, users u WHERE g.dataHoraSolicitacao >= %s AND g.dataHoraSolicitacao <= %s and u.user_id = g.user_id ORDER BY g.solicitacao_id DESC", ([dataSolicitacaoInicial], [dataSolicitacaoLimite]))
            else:
                cur.execute("SELECT dataHoraSolicitacao, tipoSolicitacao, usuarioDaSolicitacao, solicitacao_id FROM gerenciamentoUsuarios ORDER BY solicitacao_id DESC")

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
            if session['funcaoAdministrativa'] == "Gerente de Agência":
                cur.execute("SELECT g.dataHoraSolicitacao, g.tipoSolicitacao, g.usuarioDaSolicitacao, g.solicitacao_id FROM gerenciamentoUsuarios g, users u WHERE g.dataHoraSolicitacao >= %s AND g.dataHoraSolicitacao <= %s AND tipoSolicitacao = %s and u.user_id = g.user_id ORDER BY g.solicitacao_id DESC", ([dataSolicitacaoInicial], [dataSolicitacaoLimite], [tipoSolicitacao]))
            else:
                cur.execute("SELECT dataHoraSolicitacao, tipoSolicitacao, usuarioDaSolicitacao, solicitacao_id FROM gerenciamentoUsuarios WHERE dataHoraSolicitacao >= %s AND dataHoraSolicitacao <= %s AND tipoSolicitacao = %s ORDER BY solicitacao_id DESC")

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
            if session['funcaoAdministrativa'] == "Gerente de Agência":
                cur.execute("SELECT g.dataHoraSolicitacao, g.tipoSolicitacao, g.usuarioDaSolicitacao, g.solicitacao_id FROM gerenciamentoUsuarios g, users u WHERE tipoSolicitacao = %s and u.user_id = g.user_id ORDER BY g.solicitacao_id DESC", ([tipoSolicitacao]))
            else:
                cur.execute("SELECT dataHoraSolicitacao, tipoSolicitacao, usuarioDaSolicitacao, solicitacao_id FROM gerenciamentoUsuarios WHERE tipoSolicitacao = %s ORDER BY solicitacao_id DESC", ([tipoSolicitacao]))

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
            if session['funcaoAdministrativa'] == "Gerente de Agência":
                cur.execute("SELECT g.dataHoraSolicitacao, g.tipoSolicitacao, g.usuarioDaSolicitacao, g.solicitacao_id FROM gerenciamentoUsuarios g, users u WHERE u.gerente_id = %s and u.user_id = g.user_id ORDER BY g.solicitacao_id DESC", ([session['idGerente']]))
            else:
                cur.execute("SELECT dataHoraSolicitacao, tipoSolicitacao, usuarioDaSolicitacao, solicitacao_id FROM gerenciamentoUsuarios ORDER BY solicitacao_id DESC")

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
            if session['funcaoAdministrativa'] == "Gerente de Agência":
                cur.execute("SELECT g.dataHoraSolicitacao, g.tipoSolicitacao, g.usuarioDaSolicitacao, g.solicitacao_id FROM gerenciamentoUsuarios g, users u WHERE u.gerente_id = %s and u.user_id = g.user_id ORDER BY g.solicitacao_id DESC", ([session['idGerente']]))
            else:
                cur.execute("SELECT dataHoraSolicitacao, tipoSolicitacao, usuarioDaSolicitacao, solicitacao_id FROM gerenciamentoUsuarios ORDER BY solicitacao_id DESC")

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
    cur.execute("SELECT nome, contaBancaria, agenciaBancaria, saldoAtual, valorDeposito, saldoFinal, statusSolicitacao, user_id, deposito_id FROM confirmacaoDeposito WHERE solicitacao_id = %s", ([solicitacaoIdCadastro]))

    dadosUsuarioDeposito = cur.fetchone()

    app.logger.info(dadosUsuarioDeposito)

    session["nomeUsuario"] = dadosUsuarioDeposito[0]
    session["contaUsuario"] = dadosUsuarioDeposito[1]
    session["agenciaBancariaUsuario"] = dadosUsuarioDeposito[2]
    session["saldoAtualUsuario"] = dadosUsuarioDeposito[3]
    valorDepositoUsuario = dadosUsuarioDeposito[4]
    valorDepositoUsuario = float(valorDepositoUsuario)
    session["valorDepositoUsuario"] = valorDepositoUsuario
    session["saldoFinalUsuario"] = dadosUsuarioDeposito[5]
    session["statusSolicitacaoDeposito"] = dadosUsuarioDeposito[6]
    session["userIdUsuario"] = dadosUsuarioDeposito[7]
    session["depositoId"] = dadosUsuarioDeposito[8]
    statusSolicitacao = session["statusSolicitacaoDeposito"]

    #OBS: Quando um valor retorna do banco de dados, ele vem com a caracteristica descrita lá. Aqui transformamos decimal.Decimal para Float.
    cur.execute("SELECT saldoBancario, chequeEspecial FROM users WHERE contaBancaria = %s", [session["contaUsuario"]])
    retornoDadosUsuario = cur.fetchone()
    saldoAtual = retornoDadosUsuario[0]
    saldoAtual = float(saldoAtual)
    chequeEspecial = retornoDadosUsuario[1]

    #OBS: Quando um valor retorna do banco de dados, ele vem com a caracteristica descrita lá. Aqui transformamos decimal.Decimal para Float.
    cur.execute("SELECT capitalTotal FROM configBanco")
    retornoCapitalTotal = cur.fetchone()
    capitalTotalParcial = retornoCapitalTotal[0]
    capitalTotalParcial = float(capitalTotalParcial)

    try:
        cur.execute("SELECT valorNegativoAtualizado, valorPago FROM chequeEspecial WHERE user_id = %s", ([session["userIdUsuario"]]))
        retornoDadosChequeEspecial = cur.fetchone()
        valorNegativoAtualizado = retornoDadosChequeEspecial[0]
        valorPagoCheque = retornoDadosChequeEspecial[1]
    except Exception as ex:
        pass

    if request.method == "POST":
        if "confirmar" in request.form:
            #Para fazer UPDATES onde as duas variaveis precisam ser mudadas, basta utilizar o %s. Entretanto, no final como é uma Tupla, preciso informar o que substituir por meio de um parênteses EX:([x],[y]).
              
            statusSolicitacao = "Confirmada"

            if chequeEspecial == 1:

                cur = mysql.connection.cursor()
                saldoNovo = float(valorNegativoAtualizado) + float(valorPagoCheque)
                app.logger.info(saldoNovo)
                capitalTotalNovo = float(capitalTotalParcial) + float(valorPagoCheque)
                app.logger.info(capitalTotalNovo)

                if saldoNovo >= 0:
                    chequeEspecialNovo = 0
                    cur = mysql.connection.cursor()
                    cur.execute("UPDATE users SET chequeEspecial = %s WHERE user_id = %s", ([chequeEspecialNovo], [session["userIdUsuario"]]))
                    mysql.connection.commit()
                    cur.close()

                if saldoNovo < 0:
                    novoValorNegativo = float(saldoNovo)
                    cur = mysql.connection.cursor()
                    cur.execute("UPDATE chequeEspecial SET valorSaque = %s, valorNegativoAtualizado = %s WHERE user_id = %s", ([novoValorNegativo], [novoValorNegativo], [session["userIdUsuario"]]))
                    mysql.connection.commit()
                    cur.close()
            else:
                cur = mysql.connection.cursor()
                saldoNovo = float(saldoAtual) + float(valorDepositoUsuario)
                capitalTotalNovo = float(capitalTotalParcial) + float(valorDepositoUsuario)

            cur = mysql.connection.cursor()

            cur.execute("UPDATE confirmacaoDeposito SET statusSolicitacao = %s WHERE deposito_id = %s", ([statusSolicitacao], session["depositoId"]))

            cur.execute("UPDATE users SET saldoBancario = %s WHERE user_id= %s", ([float(saldoNovo)], session['userIdUsuario']))

            cur.execute("UPDATE configBanco SET capitalTotal = %s", ([float(capitalTotalNovo)]))

            cur.execute("INSERT INTO movimentacaoConta (dataHoraMovimentacao, tipoMovimentacao, movimentacao, user_id) VALUES (%s, %s, %s, %s)", (session['horaSistema'], [tipoMovimentacao], session["valorDepositoUsuario"], session['userIdUsuario']))

            if saldoNovo >= 0:
                try:
                    cur = mysql.connection.cursor()
                    cur.execute("DELETE FROM chequeEspecial WHERE user_id = %s", ([session["userIdUsuario"]]))
                    mysql.connection.commit()
                    cur.close()
                except Exception as ex:
                    pass

            mysql.connection.commit()
            cur.close()
            flash("Confirmação de depósito feita com sucesso!")
            
        else:
            statusSolicitacao = "Cancelada"
            cur = mysql.connection.cursor()
            cur.execute("UPDATE confirmacaoDeposito SET statusSolicitacao = %s", ([statusSolicitacao]))

            mysql.connection.commit()
            cur.close()
            flash("Cancelamento de depósito feito com sucesso!")
        
    return render_template("tela-confirmacao-deposito.html", titulo="Solicitações", statusSolicitacao = statusSolicitacao)

@app.route("/confirmacao-abertura", methods = ["GET", "POST"])
def confirmacaoAbertura():
    solicitacaoIdAbertura = request.args.get("solicitacaoIdAbertura")
    
    cur = mysql.connection.cursor()
    cur.execute("SELECT nome, cpf, dataAniversario, genero, endereco, tipoConta, contaBancaria, agenciaBancaria, statusSolicitacao FROM confirmacaoAbertura WHERE solicitacao_id = %s", ([solicitacaoIdAbertura]))
    dadosUsuarioFechamento = cur.fetchone()
    session["nomeUsuarioCadastro"] = dadosUsuarioFechamento[0]
    session["cpfUsuarioCadastro"] = dadosUsuarioFechamento[1]
    session["dataAniversarioAbertura"] = dadosUsuarioFechamento[2]
    session["generoAbertura"] = dadosUsuarioFechamento[3]
    session["enderecoAbertura"] = dadosUsuarioFechamento[4]
    session["tipoContaAbertura"] = dadosUsuarioFechamento[5]
    session["contaBancariaAbertura"] = dadosUsuarioFechamento[6]
    session["agenciaBancariaAbertura"] = dadosUsuarioFechamento[7]
    session["statusSolicitacaoAbertura"] = dadosUsuarioFechamento[8]
    statusSolicitacao = session["statusSolicitacaoAbertura"]

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

    return render_template("tela-abertura-conta.html", titulo="Solicitações", solicitacaoIdAbertura = solicitacaoIdAbertura, statusSolicitacao = statusSolicitacao)

@app.route("/confirmacao-fechamento", methods = ["GET", "POST"])
def confirmacaoFechamento():
    solicitacaoIdFechamento = request.args.get("solicitacaoIdFechamento")
     
    cur = mysql.connection.cursor()
    cur.execute("SELECT nome, cpf, dataAniversario, genero, endereco, contaBancaria, agenciaBancaria, statusSolicitacao FROM confirmacaoFechamento WHERE solicitacao_id = %s", ([solicitacaoIdFechamento]))
    dadosUsuarioFechamento = cur.fetchone()
    session["nomeUsuarioCadastro"] = dadosUsuarioFechamento[0]
    session["cpfUsuarioCadastro"] = dadosUsuarioFechamento[1]
    session["dataAniversarioAbertura"] = dadosUsuarioFechamento[2]
    session["generoAbertura"] = dadosUsuarioFechamento[3]
    session["enderecoAbertura"] = dadosUsuarioFechamento[4]
    session["contaBancariaAbertura"] = dadosUsuarioFechamento[5]
    session["agenciaBancariaAbertura"] = dadosUsuarioFechamento[6]
    statusSolicitacao = dadosUsuarioFechamento[7]

    if request.method == "POST":
        if "confirmar" in request.form:
            statusSolicitacao = "Fechada"

            cur = mysql.connection.cursor()
            cur.execute("UPDATE confirmacaoAbertura SET statusSolicitacao = %s WHERE contaBancaria= %s", ([statusSolicitacao], session["contaBancariaAbertura"]))
            cur.execute("UPDATE confirmacaoFechamento SET statusSolicitacao = %s WHERE contaBancaria= %s", ([statusSolicitacao], session["contaBancariaAbertura"]))
            mysql.connection.commit()
            cur.close()

            flash("Fechamento de conta feita com sucesso!")
        else:
            statusSolicitacao = "Confirmada"

            cur = mysql.connection.cursor()
            cur.execute("UPDATE confirmacaoFechada SET statusSolicitacao = %s WHERE contaBancaria= %s", ([statusSolicitacao], session["contaBancariaAbertura"]))
            mysql.connection.commit()
            cur.close()

            flash("Fechamento de conta cancelado com sucesso!")

    return render_template("tela-fechamento-conta.html", titulo="Solicitações", solicitacaoIdFechamento = solicitacaoIdFechamento, statusSolicitacao = statusSolicitacao)

@app.route("/confirmacao-alteracao-dados", methods=["GET", "POST"])
def confirmacaoAlteracao():

    solicitacaoIdAlteracao = request.args.get("solicitacaoIdAlteracao")
    
    cur = mysql.connection.cursor()
    cur.execute("SELECT user_id, nome, cpf, dataAniversario, genero, endereco, statusSolicitacao FROM confirmacaoAlteracao WHERE solicitacao_id = %s", ([solicitacaoIdAlteracao]))
    dadosUsuarioAlteracao = cur.fetchone()
    app.logger.info(dadosUsuarioAlteracao)
    session["userIdAlteracao"] = dadosUsuarioAlteracao[0]
    session["novoNomeUsuario"] = dadosUsuarioAlteracao[1]
    session["novoCpfUsuario"] = dadosUsuarioAlteracao[2]
    session["novoAniversario"] = dadosUsuarioAlteracao[3]
    session["novoGenero"] = dadosUsuarioAlteracao[4]
    session["novoEndereco"] = dadosUsuarioAlteracao[5]
    statusSolicitacao = dadosUsuarioAlteracao[6]
    

    if request.method == "POST":
        if "confirmar" in request.form:
            statusSolicitacao = "Confirmada"
            app.logger.info(statusSolicitacao)
            session["statusSolicitacao"] = statusSolicitacao
            app.logger.info([statusSolicitacao])
            cur = mysql.connection.cursor()

            cur.execute("UPDATE confirmacaoAlteracao SET statusSolicitacao = %s WHERE solicitacao_id= %s", ([statusSolicitacao], [solicitacaoIdAlteracao]))

            cur.execute("UPDATE confirmacaoAbertura SET nome = %s, cpf = %s, dataAniversario = %s, genero = %s, endereco = %s, statusSolicitacao = %s WHERE user_id= %s", (session["novoNomeUsuario"], session["novoCpfUsuario"], session["novoAniversario"], session["novoGenero"], session["novoEndereco"], [statusSolicitacao], session["userIdAlteracao"]))

            cur.execute("UPDATE users SET nome = %s, cpf = %s, dataAniversario = %s, genero = %s, endereco = %s WHERE user_id= %s", (session["novoNomeUsuario"], session["novoCpfUsuario"], session["novoAniversario"], session["novoGenero"], session["novoEndereco"], session["userIdAlteracao"]))
            mysql.connection.commit()

            cur.close()

            flash("Confirmação de alterações cadastrais feita com sucesso!")
        else:
            statusSolicitacao = "Cancelada"
            cur = mysql.connection.cursor()
            cur.execute("UPDATE confirmacaoAlteracao SET statusSolicitacao = %s WHERE alteracao_id= %s", ([statusSolicitacao], [solicitacaoIdAlteracao]))
            mysql.connection.commit()
            cur.close()
            flash("Cancelamento de alterações cadastrais feito com sucesso!")

    return render_template("solicitacao_alterar_dados.html", titulo="Solicitações", statusSolicitacao = statusSolicitacao)

@app.route("/editar-agencia", methods=["GET", "POST"])
def editarAgencia():

    cur = mysql.connection.cursor()
    cur.execute("SELECT numero_agencia from agencias")

    listaAgenciasCriadas = []

    for i in cur:
        listaAgenciasCriadas.append(i[0])

    listaAgenciasDisponiveis = []

    for x in range(1,51):
        if x <= 9:
            novaAgencia = "000" + str(x)
            listaAgenciasDisponiveis.append(novaAgencia)
        else:
            novaAgencia = "00" + str(x)
            listaAgenciasDisponiveis.append(novaAgencia)

    for i in listaAgenciasDisponiveis:
        for x in listaAgenciasCriadas:
            if x in listaAgenciasDisponiveis:
                listaAgenciasDisponiveis.remove(x)


    if request.method == 'POST':
        if "confirmar" in request.form:

            novoNumeroAgencia = request.form['numAgenciaCadastro']
            novoNumeroClientes = request.form['numeroClientes']
            novoEndAgencia = request.form['enderecoAgencia']
            
            cur = mysql.connection.cursor()
            cur.execute("UPDATE agencias SET numero_agencia = %s, numero_clientes = %s, end_agencia = %s WHERE agencia_id = %s", ([novoNumeroAgencia], [novoNumeroClientes], [novoEndAgencia], session["retornoAgenciaId"]))
            mysql.connection.commit()
            cur.close()
            flash("Dados atualizados com sucesso!")
            return redirect(url_for("editarAgencia"))
        elif "cancelar" in request.form:
            return redirect(url_for("homeGerenteGeral"))
        else:
            pass
            return redirect(url_for("editarAgencia"))

    cur = mysql.connection.cursor()
    cur.execute("SELECT numero_agencia, numero_clientes, data_criacao, end_agencia, agencia_id FROM agencias WHERE agencia_id = %s", ([session["retornoAgenciaId"]]))
    retornoDadosAgencia = cur.fetchone()
    app.logger.info(retornoDadosAgencia)
    session["retornoNumeroAgencia"] = retornoDadosAgencia[0]
    session["retornoNumeroClientes"] = retornoDadosAgencia[1]
    session["retornoNumeroDataCriacao"] = retornoDadosAgencia[2]
    session["retornoEnderecoAgencia"] = retornoDadosAgencia[3]
    return render_template("editar_agencia.html", titulo="Editar Agência", listaAgenciasDisponiveis = listaAgenciasDisponiveis)

@app.route("/lista-gerentes", methods=["GET", "POST"])
def listaGerentes():
    if session["gerenteLogado"] == False:
        return redirect (url_for("indexGerente"))
        
    if request.method == "POST":
        if "novo" in request.form:
            return redirect(url_for("novoGerenteAgencia"))
        else:
            nomeGerente = request.form.get("nomeGerente")

            cur = mysql.connection.cursor()
            cur.execute("SELECT gerente_nome, gerente_id FROM gerenteAgencia where gerente_nome = %s", ([nomeGerente]))

            retornoNomeGerente = []
            retornoIdGerente = []

            for i in cur:
                retornoNomeGerente.append(i[0])
                retornoIdGerente.append(i[1])

            colunas = ("Gerente", "Visualizar")
            dados = list(zip(retornoNomeGerente, retornoIdGerente))

            return render_template("gerentes.html", titulo="Gerentes", colunas = colunas, dados = dados)
    else:
        cur = mysql.connection.cursor()
        cur.execute("SELECT gerente_nome, gerente_id FROM gerenteAgencia")

        retornoNomeGerente = []
        retornoIdGerente = []

        for i in cur:
            retornoNomeGerente.append(i[0])
            retornoIdGerente.append(i[1])

        colunas = ("Gerente", "Visualizar")
        dados = list(zip(retornoNomeGerente, retornoIdGerente))

        return render_template("gerentes.html", titulo="Gerentes", colunas = colunas, dados = dados)

@app.route("/lista-agencias", methods=["GET", "POST"])
def listaAgencias():
    cur = mysql.connection.cursor()
    cur.execute("SELECT numero_agencia, agencia_id FROM agencias")

    retornoNumAgencia = []
    retornoIdAgencia = []

    for i in cur:
        retornoNumAgencia.append(i[0])
        retornoIdAgencia.append(i[1])

    colunas = ("Agência", "Visualizar")
    dados = list(zip(retornoNumAgencia, retornoIdAgencia))

    return render_template("tela_agencias.html", titulo="Agências", colunas = colunas, dados = dados)

@app.route("/info-gerente", methods=["GET", "POST"])
def infoGerente():

    idGerente = request.args.get("idGerente")
    cur = mysql.connection.cursor()
    cur.execute("SELECT gerente_nome, gerente_cpf, gerente_nasc, gerente_genero, gerente_end,num_matricula, num_agencia, data_criacao, gerente_id from gerenteAgencia where gerente_id =%s", (idGerente))
    retornoGerenteAgencia = cur.fetchone()
    app.logger.info(retornoGerenteAgencia)
    session["nomeRetornoGerenteAgencia"] = retornoGerenteAgencia[0]
    session["cpfRetornoGerenteAgencia"] = retornoGerenteAgencia[1]
    session["nascRetornoGerenteAgencia"] = retornoGerenteAgencia[2]
    session["generoRetornoGerenteAgencia"] = retornoGerenteAgencia[3]
    session["endRetornoGerenteAgencia"] = retornoGerenteAgencia[4]
    session["matriculaRetornoGerenteAgencia"] = retornoGerenteAgencia[5]
    session["numAgenciaRetornoGerenteAgencia"] = retornoGerenteAgencia[6]
    session["dataCriacaoRetornoGerenteAgencia"] = retornoGerenteAgencia[7]
    session["retornoGerenteId"] = retornoGerenteAgencia[8]
    
    return render_template("info_gerente.html", titulo="Gerente") 

@app.route("/info-agencia", methods=["GET", "POST"])
def infoAgencia():
    idAgencia = request.args.get("idAgencia")
    #vamos trazer as info do BD e transformalas em session
    cur = mysql.connection.cursor()
    cur.execute("SELECT numero_agencia, numero_clientes, numero_total_clientes, data_criacao, end_agencia, agencia_id FROM agencias WHERE agencia_id = %s", (idAgencia))
    retornoDadosAgencia = cur.fetchone()
    app.logger.info(retornoDadosAgencia)
    session["retornoNumeroAgencia"] = retornoDadosAgencia[0]
    session["retornoNumeroClientes"] = retornoDadosAgencia[1]
    session["retornoNumeroMaximoClientes"] = retornoDadosAgencia[2]
    session["retornoNumeroDataCriacao"] = retornoDadosAgencia[3]
    session["retornoEnderecoAgencia"] = retornoDadosAgencia[4]
    session["retornoAgenciaId"] = retornoDadosAgencia[5]

    return render_template("info_agencia.html", Título="Agência")

@app.route("/home-gerente-geral", methods=["GET", "POST"])
def homeGerenteGeral():
    if session["gerenteLogado"] == False:
        return redirect (url_for("indexGerenteGeral"))
    
    cur = mysql.connection.cursor()
    cur.execute("SELECT capitalTotal, taxaJurosPoupanca, taxaJurosCheque from configBanco")
    retornoConfigBanco = cur.fetchone()
    session["capitalTotal"] = retornoConfigBanco[0]
    session["taxaJurosPoupanca"] = retornoConfigBanco[1]
    session["taxaJurosCheque"] = retornoConfigBanco[2]

    if request.method == 'POST':
        userDetails = request.form
        jurosPoupancaEditado = userDetails["jurosPoupancaEditado"]
        jurosChequeEditado = userDetails["jurosChequeEditado"]

        cur = mysql.connection.cursor()
        cur.execute("UPDATE configBanco SET taxaJurosPoupanca = %s, taxaJurosCheque = %s", (jurosPoupancaEditado, jurosChequeEditado))
        #MySQLdb.ProgrammingError: not all arguments converted during bytes formatting -> colocar []
        cur.execute("UPDATE poupanca SET valorTaxa = %s", ([jurosPoupancaEditado]))
        cur.connection.commit()
        cur.close()
        #OBS: Usar para os outros sessions!!
        flash("Configuração de taxa atualizada com sucesso!")
        return redirect(url_for("homeGerenteGeral"))

    return render_template("home_gg.html")

@app.route("/cadastroGerente", methods=["GET", "POST"])
def cadastroGerente():

    senhaGerenteAgencia=123
   
    numero = []
    for i in range(1, 6):
        numero.append(random.randint(0, 9))
    matriculaGerenteAgencia="".join(map(str,numero))

    cur = mysql.connection.cursor()
    cur.execute("SELECT numero_agencia from agencias")

    listaAgenciasDisponiveis = []

    for i in cur:
        listaAgenciasDisponiveis.append(i[0])
    

    if request.method == "POST":
        if "confirmar" in request.form:
            name = request.form["nome"]
            cpf = request.form["cpf"]
            dataAniversario = request.form["dataAniversario"]
            genero = request.form["genero"]
            endereco = request.form["endereco"]
            agencia = request.form["numAgencia"]
            session.pop("horaSistema", None)
            session["horaSistema"] = dataAgora()

            if not name or not cpf or not dataAniversario or not genero or not endereco or not agencia:
                flash("Preencha todos os campos do formulário!")
                return redirect (url_for("cadastroGerente"))

            cur = mysql.connection.cursor()
            cur.execute("INSERT INTO gerenteAgencia (gerente_nome, gerente_cpf, gerente_nasc, gerente_genero, gerente_end, num_agencia, num_matricula, num_senha, data_criacao) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s)",(name, cpf, dataAniversario, genero, endereco, agencia, matriculaGerenteAgencia, senhaGerenteAgencia, session["horaSistema"]))
            mysql.connection.commit()
            cur.close()

            
            cur = mysql.connection.cursor()
            cur.execute("SELECT gerente_nome, gerente_cpf, gerente_nasc, gerente_genero, gerente_end, num_matricula, num_agencia, data_criacao, gerente_id FROM gerenteAgencia WHERE num_matricula = %s", ([matriculaGerenteAgencia]))
            retornoDadosGerente = cur.fetchone()

            session["nomeGerenteAgencia"] = retornoDadosGerente[0]
            session["cpfGerenteAgencia"] = retornoDadosGerente[1]
            session["nascGerenteAgencia"] = retornoDadosGerente[2]
            session["generoGerenteAgencia"] = retornoDadosGerente[3]
            session["endGerenteAgencia"] = retornoDadosGerente[4]
            session["matriculaGerenteAgencia"] = retornoDadosGerente[5]
            numAgenciaNova = retornoDadosGerente[6]
            session["numAgenciaGerenteAgencia"] = numAgenciaNova
            session["dataCriacaoGerenteAgencia"] = retornoDadosGerente[7]
            idNovoGerente = retornoDadosGerente[8]
            session["gerenteAgenciaId"] = idNovoGerente

            app.logger.info(idNovoGerente,numAgenciaNova)

            cur = mysql.connection.cursor()
            cur.execute("UPDATE agencias SET gerente_id = %s WHERE numero_agencia = %s", ([idNovoGerente], [numAgenciaNova]))
            mysql.connection.commit()
            cur.close()

            flash("Cadastro realizado com sucesso!")
            return redirect(url_for("cadastroGerente"))
    return render_template("novo_gerente.html", titulo="Novo Gerente", listaAgenciasDisponiveis = listaAgenciasDisponiveis)

@app.route("/editar-gerentes", methods=["GET", "POST"])
def editarGerentes():
    
    cur = mysql.connection.cursor()
    cur.execute("SELECT numero_agencia from agencias")

    listaAgenciasDisponiveis = []

    for i in cur:
        listaAgenciasDisponiveis.append(i[0])

    if request.method == 'POST':
        if "confirmar" in request.form:

            novoNomeGerente = request.form['nomeGerenteCadastro']
            novoCpfGerente = request.form['cpfGerenteCadastro']
            novoNascGerente = request.form['nascGerenteCadastro']
            novoGeneroGerente = request.form['generoGerenteCadastro']
            novoEndGerente = request.form['endGerenteCadastro']
            novoNumMatriculaGerente = request.form['matriculaGerenteCadastro']
            novoNumAgenciaGerente = request.form['numAgenciaCadastro']

            cur = mysql.connection.cursor()
            cur.execute("SELECT gerente_id from gerenteAgencia where num_matricula = %s", ([session["matriculaRetornoGerenteAgencia"]]))
            idGerenteRetorno = cur.fetchone()
            app.logger.info(idGerenteRetorno)
            idGerenteAgencia = idGerenteRetorno[0]

            cur.execute("UPDATE gerenteAgencia SET gerente_nome = %s, gerente_cpf = %s, gerente_nasc = %s, gerente_genero = %s, gerente_end = %s, num_matricula = %s, num_agencia = %s WHERE gerente_id = %s", ([novoNomeGerente], [novoCpfGerente], [novoNascGerente], [novoGeneroGerente], [novoEndGerente], [novoNumMatriculaGerente], [novoNumAgenciaGerente], [idGerenteAgencia]))
            mysql.connection.commit()
            cur.close()

            cur = mysql.connection.cursor()
            cur.execute("SELECT gerente_nome, gerente_cpf, gerente_nasc, gerente_genero, gerente_end, num_matricula, num_agencia, data_criacao, gerente_id FROM gerenteAgencia WHERE num_matricula = %s", ([novoNumMatriculaGerente]))
            retornoDadosGerente = cur.fetchone()

            session["nomeGerenteAgencia"] = retornoDadosGerente[0]
            session["cpfGerenteAgencia"] = retornoDadosGerente[1]
            session["nascGerenteAgencia"] = retornoDadosGerente[2]
            session["generoGerenteAgencia"] = retornoDadosGerente[3]
            session["endGerenteAgencia"] = retornoDadosGerente[4]
            session["matriculaGerenteAgencia"] = retornoDadosGerente[5]
            session["numAgenciaGerenteAgencia"] = retornoDadosGerente[6]
            session["dataCriacaoGerenteAgencia"] = retornoDadosGerente[7]
            session["gerenteAgenciaId"] = retornoDadosGerente[8]

            flash("Dados atualizados com sucesso!")
            return redirect(url_for("editarGerentes"))
        else:
            return redirect(url_for("editarGerentes"))

    cur = mysql.connection.cursor()
    cur.execute("SELECT gerente_nome, gerente_cpf, gerente_nasc, gerente_genero, gerente_end, num_matricula, num_agencia, data_criacao from gerenteAgencia where gerente_id =%s", ([session["retornoGerenteId"]]))
    retornoGerenteAgencia = cur.fetchone()
    app.logger.info(retornoGerenteAgencia)
    session["nomeRetornoGerenteAgencia"] = retornoGerenteAgencia[0]
    session["cpfRetornoGerenteAgencia"] = retornoGerenteAgencia[1]
    session["nascRetornoGerenteAgencia"] = retornoGerenteAgencia[2]
    session["generoRetornoGerenteAgencia"] = retornoGerenteAgencia[3]
    session["endRetornoGerenteAgencia"] = retornoGerenteAgencia[4]
    session["matriculaRetornoGerenteAgencia"] = retornoGerenteAgencia[5]
    session["numAgenciaRetornoGerenteAgencia"] = retornoGerenteAgencia[6]
    session["dataCriacaoRetornoGerenteAgencia"] = retornoGerenteAgencia[7] 
    
    return render_template("editar_gerente.html", titulo="Editar Gerente", listaAgenciasDisponiveis = listaAgenciasDisponiveis)

@app.route("/cadastroAgencia", methods=["GET", "POST"])
def cadastroAgencia():

    cur = mysql.connection.cursor()
    cur.execute("SELECT numero_agencia from agencias")

    listaAgenciasCriadas = []

    for i in cur:
        listaAgenciasCriadas.append(i[0])

    listaAgenciasDisponiveis = []

    for x in range(1,51):
        if x <= 9:
            novaAgencia = "000" + str(x)
            listaAgenciasDisponiveis.append(novaAgencia)
        else:
            novaAgencia = "00" + str(x)
            listaAgenciasDisponiveis.append(novaAgencia)

    for i in listaAgenciasDisponiveis:
        for x in listaAgenciasCriadas:
            if x in listaAgenciasDisponiveis:
                listaAgenciasDisponiveis.remove(x)

    if request.method == "POST":
        if "cadastrar" in request.form:
            endereco = request.form["enderecoAgencia"] 
            numAgencia = request.form["numAgencia"]
            app.logger.info(numAgencia)
            numUsuarios = 0
            numTotalClientes = 10

            session.pop("horaSistema", None)
            session["horaSistema"] = dataAgora()

            if not endereco or not numAgencia:
                flash("Preencha todos os campos do formulário!")
                return redirect (url_for("cadastroAgencia"))

            cur = mysql.connection.cursor()
            cur.execute("INSERT INTO agencias (numero_agencia, numero_clientes, numero_total_clientes, data_criacao, end_agencia) VALUES(%s, %s, %s, %s, %s)",(numAgencia, numUsuarios, numTotalClientes, session["horaSistema"], endereco))
            mysql.connection.commit()
            cur.close()

            flash("Agência cadastrada com sucesso!")

            return redirect(url_for("cadastroAgencia"))

    return render_template("nova_agencia.html", titulo="Nova Agência", listaAgenciasDisponiveis = listaAgenciasDisponiveis)


@app.route("/poupanca", methods=["GET", "POST"])
def poupanca():

    cur = mysql.connection.cursor()
    cur.execute("SELECT saldoBancario FROM users WHERE user_id = %s", [session['idUsuario']])
    retornoSaldoAtual = cur.fetchone()
    saldoAtualUsuario = retornoSaldoAtual[0]
    session.pop('saldoUsuario', None)
    saldoFormatado = '{0:.2f}'.format(saldoAtualUsuario)
    session['saldoUsuario'] = saldoFormatado.replace('.',',')

    session.pop('montanteParaReceber', None)

    #try para tentar trazer os dados da poupança, caso o usuario já estiver começado a poupança

    try:
        cur = mysql.connection.cursor()
        cur.execute("SELECT valorInicial, dataInicial, valorTaxa, poupanca_id FROM poupanca WHERE user_id = %s", ([session["idUsuario"]]))
        retornoDadosPoupanca = cur.fetchone()

        retornoValorInicial = retornoDadosPoupanca[0]
        retornoValorInicial = float(retornoValorInicial)
        session["valorInicialUsuarioPoupanca"] = retornoValorInicial

        dataInicialUsuarioPoupanca = retornoDadosPoupanca[1]
        session["dataInicialUsuarioPoupanca"] = dataInicialUsuarioPoupanca

        valorTaxaPoucanca = retornoDadosPoupanca[2]
        valorTaxaPoucanca = float(valorTaxaPoucanca)
        session["valorTaxaUsuarioPoupanca"] = valorTaxaPoucanca

        idPoupancaUsuario = retornoDadosPoupanca[3]

        #editando a data para o timestampdiff
        dataInicialUsuarioPoupanca = str(dataInicialUsuarioPoupanca)
        dataInicialChequeEditado = dataInicialUsuarioPoupanca[-4:] + dataInicialUsuarioPoupanca[2:6] + dataInicialUsuarioPoupanca[0:2]
        dataInicialChequeEditado = dataInicialChequeEditado.replace("/","-")

        with open("config.json", "r") as outfile:
            viagemTemporal = json.load(outfile)
        
        viagemTemporal = str(viagemTemporal)
        viagemTemporalEditado = viagemTemporal[-4:] + viagemTemporal[2:6] + viagemTemporal[0:2]
        viagemTemporalEditado = viagemTemporalEditado.replace("/","-")

        app.logger.info(dataInicialChequeEditado, viagemTemporalEditado)

        cur = mysql.connection.cursor()
        cur.execute("SELECT TIMESTAMPDIFF(MONTH,%s,%s)", ([str(dataInicialChequeEditado)], [str(viagemTemporalEditado)]))
        retornoDiferencaMeses = cur.fetchone()
        mesesCobranca = retornoDiferencaMeses[0]

        app.logger.info(mesesCobranca)

        montanteParaReceber = retornoValorInicial * ((1 + valorTaxaPoucanca) ** mesesCobranca)
        montanteParaReceber = '{0:.2f}'.format(montanteParaReceber)
        app.logger.info(montanteParaReceber)

        session.pop('montanteParaReceber', None)
        session["montanteParaReceber"] = montanteParaReceber
    except Exception as ex:
        pass

    #trecho para quando o usuario começar a poupança    
    if request.method == 'POST':
        if "poupar" in request.form:
            try:
                cur = mysql.connection.cursor()
                cur.execute("SELECT poupanca_id FROM poupanca WHERE user_id = %s", ([session["idUsuario"]]))
                retornoDadosPoupanca = cur.fetchone()
                idPoupancaUsuario = retornoDadosPoupanca[0]
            except Exception as ex:
                idPoupancaUsuario = None

            if idPoupancaUsuario:
                userDetails = request.form
                valorInicial = userDetails["valorPoupar"]
                app.logger.info(valorInicial)

                session.pop("dataInicial", None)
                dataInicial = dataAgora()
                session["dataInicial"] = dataInicial

                cur = mysql.connection.cursor()

                #trazendo valor da taxa poupança da tabela configBanco
                cur.execute("SELECT taxaJurosPoupanca FROM configBanco")
                retornoJurosPoupanca = cur.fetchone()
                jurosPoupanca = retornoJurosPoupanca[0]
                jurosPoupanca = float(jurosPoupanca)

                cur.execute("SELECT saldoBancario FROM users WHERE user_id = %s", ([session["idUsuario"]]))
                retornoSaldoUsuario = cur.fetchone()
                saldoUsuario = retornoSaldoUsuario[0]
                app.logger.info(saldoUsuario)

                if float(valorInicial) > float(saldoUsuario):
                    flash("Faça um depósito na poupança equivalente ao seu saldo em conta!")
                    return redirect(url_for("poupanca"))
                if float(valorInicial) <= 0:
                    flash("Apenas valores positivos e acima de 0 Reais são permitidos!")
                    return redirect(url_for("poupanca"))
                if not valorInicial:
                    flash("Digite um valor para depositar na poupança!")

                saldoNovoUsuario = float(saldoUsuario) - float(valorInicial)
                app.logger.info(saldoNovoUsuario)

                novoValorInicial = float(retornoValorInicial) + float(valorInicial)

                cur.execute("UPDATE users SET saldoBancario = %s WHERE user_id = %s", ([saldoNovoUsuario], [session["idUsuario"]]))

                cur.execute("UPDATE poupanca SET valorInicial = %s WHERE user_id = %s", ([novoValorInicial], session["idUsuario"]))

                mysql.connection.commit()
                cur.close()

                flash("Adição a poupança confirmada com sucesso!")
                return redirect(url_for("poupanca"))
            else:

                userDetails = request.form
                valorInicial = userDetails["valorPoupar"]
                app.logger.info(valorInicial)

                session.pop("dataInicial", None)
                dataInicial = dataAgora()
                session["dataInicial"] = dataInicial

                cur = mysql.connection.cursor()

                #trazendo valor da taxa poupança da tabela configBanco
                cur.execute("SELECT taxaJurosPoupanca FROM configBanco")
                retornoJurosPoupanca = cur.fetchone()
                jurosPoupanca = retornoJurosPoupanca[0]
                jurosPoupanca = float(jurosPoupanca)

                cur.execute("SELECT saldoBancario FROM users WHERE user_id = %s", ([session["idUsuario"]]))
                retornoSaldoUsuario = cur.fetchone()
                saldoUsuario = retornoSaldoUsuario[0]
                app.logger.info(saldoUsuario)

                if float(valorInicial) > float(saldoUsuario):
                    flash("Faça um depósito na poupança equivalente ao seu saldo em conta!")
                    return redirect(url_for("poupanca"))
                if float(valorInicial) <= 0:
                    flash("Apenas valores positivos e acima de 0 Reais são permitidos!")
                    return redirect(url_for("poupanca"))
                if not valorInicial:
                    flash("Digite um valor para depositar na poupança!")

                saldoNovoUsuario = float(saldoUsuario) - float(valorInicial)
                app.logger.info(saldoNovoUsuario)

                cur.execute("UPDATE users SET saldoBancario = %s WHERE user_id = %s", ([saldoNovoUsuario], [session["idUsuario"]]))

                cur.execute("INSERT INTO poupanca (valorInicial, dataInicial, valorTaxa, user_id, config_id) VALUES (%s, %s, %s, %s, %s)", ([valorInicial], session["dataInicial"], [jurosPoupanca], session["idUsuario"], 1))

                mysql.connection.commit()
                cur.close()

                flash("Poupança confirmada com sucesso!")
                return redirect(url_for("poupanca"))
        else:

            cur = mysql.connection.cursor()

            cur.execute("SELECT saldoBancario FROM users WHERE user_id = %s", ([session["idUsuario"]]))
            retornoSaldoUsuario = cur.fetchone()
            saldoUsuario = retornoSaldoUsuario[0]
            app.logger.info(saldoUsuario)

            novoSaldoRetirada = float(saldoUsuario) + float(montanteParaReceber)

            cur.execute("UPDATE users SET saldoBancario = %s where user_id = %s", ([novoSaldoRetirada], [session["idUsuario"]]))

            cur.execute("UPDATE poupanca SET dataFinal = %s, valorAtualizado = %s where user_id = %s", ([viagemTemporalEditado], [montanteParaReceber], [session["idUsuario"]]))

            cur.execute("SELECT capitalTotal FROM configBanco")
            retornoCapitalTotal = cur.fetchone()
            capitalTotalParcial = retornoCapitalTotal[0]
            capitalTotalParcial = float(capitalTotalParcial)

            capitalTotalNovo = float(capitalTotalParcial) - float(montanteParaReceber)

            cur.execute("UPDATE configBanco SET capitalTotal = %s", ([float(capitalTotalNovo)]))

            cur.execute("DELETE FROM poupanca WHERE user_id = %s", ([session["userIdUsuario"]]))

            mysql.connection.commit()
            cur.close()

            session.pop('montanteParaReceber', None)

            flash("Poupança retirada com sucesso!")
            return redirect(url_for("poupanca"))

    return render_template("poupanca.html", titulo = "Poupança")

#Comando inicia automaticamente o programa, habilitando o debug sempre que algo for atualizado!
app.run(debug=True)