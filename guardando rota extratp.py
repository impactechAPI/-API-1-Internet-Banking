
    try:
        #Se o usuario clicar em Pesquisar retorna ao HTML a tabela contendo o conteúdo pesquisado.
        if request.method == "POST" and "pesquisar" in request.form:
            #O type date do HTML retorna o form do usuario no formato YYYY-MM-DD, foi preciso alterar "-" por "/" e "ano" por "dia"
            dataMovimentacaoInicial = request.form.get("data-inicial")
            dataMovimentacaoInicial = dataMovimentacaoInicial[-2:] + dataMovimentacaoInicial[4:8] + dataMovimentacaoInicial[0:4]
            dataMovimentacaoInicial = dataMovimentacaoInicial.replace("-","/")
            #O type date do HTML retorna o form do usuario no formato YYYY-MM-DD, foi preciso alterar "-" por "/" e "ano" por "dia"
            dataMovimentacaoLimite = request.form.get("data-limite")
            dataMovimentacaoLimite = dataMovimentacaoLimite[-2:] + dataMovimentacaoLimite[4:8] + dataMovimentacaoLimite[0:4]
            dataMovimentacaoLimite = dataMovimentacaoLimite.replace("-","/")
            #Estava retornando deposito, sem acento, acrescentei o acento pois será feito um query no DB através dessa variável
            tipoTransacao = request.form.get("tipo-transacao")
            if tipoTransacao == "deposito":
                tipoTransacao = tipoTransacao[0:3] + "ó" + tipoTransacao[4:]

            #Pegando as variaveis do Banco de Dados segundo os dados informados pelo Usuário x

            #Se houver dados em dataMovimentacao e não houver em tipoTransacao, mostrar a dataMovimentacao selecionada para todos os tipos de Transacao
            if dataMovimentacaoInicial and dataMovimentacaoLimite and tipoTransacao == "todos":
                cur = mysql.connection.cursor()
                cur.execute("SELECT dataHoraMovimentacao, movimentacao, tipoMovimentacao FROM movimentacaoConta WHERE user_id = %s AND dataHoraMovimentacao >= %s AND dataHoraMovimentacao <= %s", (session['idUsuario'], [dataMovimentacaoInicial], [dataMovimentacaoLimite]))

                app.logger.info(cur)

                dataMovimentacao = []
                movimentacao = []
                tipoMovimentacao = []

                for i in cur:
                    dataMovimentacao.append(i[0])
                    movimentacao.append(i[1])
                    tipoMovimentacao.append(i[2])

                tabelaMovimentacao = pd.DataFrame(list(zip(dataMovimentacao, movimentacao, tipoMovimentacao)), columns =['Data','Movimentação', 'Tipo de Movimentação'])

                if request.method == "POST" and "imprimir" in request.form:
                    extratoTXT = tabelaMovimentacao.to_numpy()
                    numpy.savetxt("extrato.txt", extratoTXT)

                return render_template("tela-extrato.html", tabelas=[tabelaMovimentacao.to_html(index=False)], titulos=tabelaMovimentacao.columns.values)

            #Se a dataMovimentacao e o tipoTransacao forem especificados, mostrar a dataMovimentacao e o tipo de Transacao especificado
            elif dataMovimentacaoInicial and dataMovimentacaoLimite and tipoTransacao != "todos":
                cur = mysql.connection.cursor()
                cur.execute("SELECT dataHoraMovimentacao, movimentacao, tipoMovimentacao FROM movimentacaoConta WHERE user_id = %s AND dataHoraMovimentacao >= %s AND dataHoraMovimentacao <= %s AND tipoMovimentacao = %s", (session['idUsuario'], [dataMovimentacaoInicial], [dataMovimentacaoLimite], [tipoTransacao]))

                app.logger.info(cur)

                dataMovimentacao = []
                movimentacao = []
                tipoMovimentacao = []

                for i in cur:
                    dataMovimentacao.append(i[0])
                    movimentacao.append(i[1])
                    tipoMovimentacao.append(i[2])

                tabelaMovimentacao = pd.DataFrame(list(zip(dataMovimentacao, movimentacao, tipoMovimentacao)), columns =['Data','Movimentação', 'Tipo de Movimentação'])

                if request.method == "POST" and "imprimir" in request.form:
                    extratoTXT = tabelaMovimentacao.to_numpy()
                    numpy.savetxt("extrato.txt", extratoTXT)

                return render_template("tela-extrato.html", tabelas=[tabelaMovimentacao.to_html(index=False)], titulos=tabelaMovimentacao.columns.values)

            #Se não for especificado nenhum dado para dataMovimentacao, mas ser para o tipoTransacao, mostrar todos os dados do tipoTransacao em todas as datas
            elif not dataMovimentacaoInicial and not dataMovimentacaoLimite and tipoTransacao != "todos":
                cur = mysql.connection.cursor()
                cur.execute("SELECT dataHoraMovimentacao, movimentacao, tipoMovimentacao FROM movimentacaoConta WHERE user_id = %s AND tipoMovimentacao = %s", (session['idUsuario'], [tipoTransacao]))

                app.logger.info(cur)

                dataMovimentacao = []
                movimentacao = []
                tipoMovimentacao = []

                for i in cur:
                    dataMovimentacao.append(i[0])
                    movimentacao.append(i[1])
                    tipoMovimentacao.append(i[2])

                tabelaMovimentacao = pd.DataFrame(list(zip(dataMovimentacao, movimentacao, tipoMovimentacao)), columns =['Data','Movimentação', 'Tipo de Movimentação'])

                if request.method == "POST" and "imprimir" in request.form:
                    extratoTXT = tabelaMovimentacao.to_numpy()
                    numpy.savetxt("extrato.txt", extratoTXT)

                return render_template("tela-extrato.html", tabelas=[tabelaMovimentacao.to_html(index=False)], titulos=tabelaMovimentacao.columns.values)

        #Se não for aberto uma pesquisa pelo usuário, abre todas as movimentações do usuario que estão no DB.
        else:
            cur = mysql.connection.cursor()
            cur.execute("SELECT dataHoraMovimentacao, movimentacao, tipoMovimentacao FROM movimentacaoConta WHERE user_id = %s", [session['idUsuario']])

            app.logger.info(cur)

            dataMovimentacao = []
            movimentacao = []
            tipoMovimentacao = []

            for i in cur:
                dataMovimentacao.append(i[0])
                movimentacao.append(i[1])
                tipoMovimentacao.append(i[2])

            tabelaMovimentacao = pd.DataFrame(list(zip(dataMovimentacao, movimentacao, tipoMovimentacao)), columns = ['Data','Movimentação', 'Tipo de Movimentação'])

            if request.method == "POST" and "imprimir" in request.form:
                extratoTXT = tabelaMovimentacao.to_numpy()
                numpy.savetxt("extrato.txt", extratoTXT)

            return render_template("tela-extrato.html", tabelas=[tabelaMovimentacao.to_html(index=False)], titulos=tabelaMovimentacao.columns.values)
            
    except Exception as ex:
        return render_template("tela-extrato.html")