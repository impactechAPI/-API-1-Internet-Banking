<br>
<h1 align="center"> FATEC Profº Jessen Vidal, SJC - 1º Semestre DSM </h1>

<p align="center">
    <a href="#sobre">Sobre</a> _ 
    <a href="#backlogs">Backlogs</a> _ 
    <a href="#user-stories">User Stories</a> _  
    <a href="#prototipo">Protótipo</a> _ 
    <a href="#tecnologias">Tecnologias</a> _ 
    <a href="#equipe">Equipe</a> 
</p>
   
<span id="sobre">

## Sobre o projeto

O desenvolvimento do projeto tem como objetivo a criação de um sistema de **Internet Banking** com algumas funcionalidades básicas de todo banco, online ou físico, como: abertura de contas em agências, realizar depósitos, saques, transferências, visualizar extrato de transações, atualização de dados cadastrais, crédito especial para clientes e solicitação de fechamento de contas.

>Projeto em desenvolvimento seguindo a metodologia ágil SCRUM.<br><br>
 

### Executando a aplicação


```powershell

> Baixar e instalar o Python (https://www.python.org/downloads/).

> Baixar os arquivos deste repositório ou clonar para seu próprio Github.

> Instalar os requisitos básicos executando o comando abaixo no terminal:
 pip install -r requirements.txt

> Execute a aplicação via IDE
 python app.py
 
 > No terminal do seu IDE, execute o comando: 
 flask --app app run

> O site abrirá no link: http://localhost:5000/
```

<span id="backlogs">

## Backlogs

### Backlog do Produto

### Requisitos Funcionais e Não Funcionais

| User Story | Item | ID | Sprint | 
| -- | --- | --- | --- |
| US 01 | Sistema de abertura de conta e cadastro de usuário comum | RF 3 | 01 |
| US 02 | Sistema de saque e depósito | RF 3 | 01 |
| US 03 | Sistema de login | ----- | 01 |
| US 05 | Autorizações de usuário gerente de agência | RF 02 | 02 |
| US 07 | Implementar extrato e comprovantes | RF 13 | 02 |
| US 08 | Sistema de transferência de valores | RF 03 | 02 |
| US 09 | Consulta e alteração de informações pessoais | RF 03 | 03 |
| US 10 | Sistema de fechamento de conta | RF 03 | 03 |
| US 11 | Sistema responsivo e intuitivo | RN.U.01/03 | 03 |
| US 06 | Autorizações de usuário gerente geral | RF 01 | 03 |
| US 04 | Sistema de cheque especial | RF 12/13 | 04 |
| US 12 | Juros ajustáveis | RF 13 | 04 |



### Backlog das Sprints

#### Sprint 1

| Item | Descrição                  |
| - | :------------------------- |
| 01 | Wireframe |
| 02 | Protótipo navegavel |
| 03 | Levantamento de requisitos |
| 04 | Desenvolvimento Front-End |
| 05 | Desenvolvimento Back-End |
| 06 | Repositório |

#### Sprint 2

| Item | Descrição                  |
| - | :---------------------------- |
| 01 | Sistema de Gerente de Agencia |
| 02 | Interfaces do Gerente de Agencia |
| 03 | Emissão de comprovantes de saque |
| 04 | Emissão de comprovantes de depósito |
| 05 | Emissão de extrato |
| 06 | Confirmação de depósito em conta |
| 07 | Confirmação de abertura de conta |


<span id="user-stories">

## User Stories

| Código | Quem       | O que?                                                                                                                                                   | Critério                                                |
| :----: | :--------- | :------------------------------------------------------------------------------------------------------------------------------------------------------- | :-------------------------------------------------- |
|  01   | Usuário | Como usuário comum, desejo solicitar abertura de uma conta bancária, para organizar minha vida financeira. | Após solicitação, a conta só é criada perante confirmação do gerente de agência. |
|  02   | Usuário | Como usuário comum, desejo fazer depósitos e saques em minha conta, para fins de movimentação de valores.| O valor só é atrelado a conta do usuário após confirmação do gerente de agência. O saque só poderá ser efetuado perante verificação correspondente a disponibilidade de valores do banco. |
|  03   | Usuário | Como usuário do sistema, desejo fazer login, para entrar e ter acesso à minha conta. | O login só será feito após criação de conta no banco passiva de aprovação do Gerente de Agência. |
|  04   | Usuário | Como usuário comum, desejo ter acesso a crédito (cheque especial), para ter crédito disponibilizado na conta corrente quando não houver saldo suficiente. | Entra em situação de **cheque especial** o cliente que efetuar um saque que extrapole o valor do saldo em sua conta. Um cliente que entra em situação de contratação de cheque especial, ao efetuar um depósito em sua conta, terá o valor do cheque especial automaticamente debitado, acrescido de juros compostos, calculados em base diária.|
|  05   | Usuário | Como gerente de agência, desejo confirmar abertura e fechamento de conta, alterações cadastrais e depósitos em espécie de usuário comum, para fins de conferência e verificação de possíveis inconsistências nos dados.| No caso de existência de saldo na conta em encerramento, deve-se confirmar o débito correspondente – equivalente a um saque.|
|  06   | Usuário | Como **gerente geral**, desejo gerenciar gerentes de agência e alterar dados referentes à agências, para fins de controle de funcionários e atualização de informações.  | Somente o **gerente geral** pode gerenciar usuários do tipo gerente de agência. Somente o **gerente geral** pode alterar informações referentes a uma agência. |
|  07   | Usuário | Como usuário comum, desejo visualizar e baixar meu extrato e comprovantes de transações, para fins de  consulta e verificação. | O extrato deverá ser disponibilizado para visualização a quarquer momento. Os comprovantes de operações devem ser emitidos imediatamente após a sua execução. Os comprovantes devem possuir um formato apropriado para impressão em papel e, opcionalmente, a conversão para um arquivo .txt ou PDF. Os arquivos gerados devem possuir um formato de alinhamento que facilite a leitura dos valores, detalhamentos, etc.|
|  08   | Usuário | Como usuário comum, desejo fazer transferências em minha conta, para fins de movimentação de valores.| Ter saldo disponível em conta. Caso contrário, poderá entrar em situação de cheque especial. |
|  09   | Usuário | Como usuário comum, desejo ter acesso às informações referentes à minha conta e, se preciso, solicitar alteração dos meus dados, para poder consultá-los e mantê-los atualizados. | Gerente de Agência aprovar as alterações |
|  10   | Usuário | Como usuário comum, desejo solicitar o fechamento da minha conta bancária, para poder excluir meus dados do sistema. | Após solicitação, a conta só é encerrada perante confirmação do gerente de agência. |
|  11   | Usuário | Como usuário comum, desejo um sistema intuitivo, de fácil acesso e que seja responsivo, para facilitar a navegação entre as aplicações e poder acessar a partir de qualquer dispositivo. | A interface deve possuir navegação intuitiva (acesso à informação com poucos “cliques”, metáforas, etc.). A interface deve manter a coerência das informações mesmo quando utilizada em um computador de mesa ou em um dispositivo móvel tal como um celular. |
|  12   | Usuário | Como gerente geral, desejo configurar taxas de juros, para eventuais atualizações de valores. | Aplicar taxas condizentes com a realidade. |

<span id="prototipo">

## Protótipo

Clicando [aqui](https://www.figma.com/file/fTVQuAtVUTT97mvjmaft1Q/Untitled-(Copy)?node-id=0%3A1) é possível ver as páginas e um protótipo navegavel no Figma.

![](/static/icones/GIF_API_0.gif)


![](/static/icones/GIF_API_1.gif)

Confirmação de abertura de conta:

![](/static/icones/confirmaçao_abertura.gif)

Confirmação de depósito:

![](/static/icones/confirmacao_deposito.gif)

Comprovante de depósito:

![](/static/icones/deposito_comprovante.gif)

Comprovante de saque:

![](/static/icones/saque_comprovante.gif)

Extrato de conta:

![](/static/icones/extrato_conta.gif)


<span id="tecnologias">

##  Tecnologias

Essas foram as tecnologias utilizadas, até agora, para desenvolvimento da aplicação:

- [HTML](https://developer.mozilla.org/pt-BR/docs/Web/HTML): Estrutura das páginas do site
- [CSS](https://developer.mozilla.org/pt-BR/docs/Web/CSS): Estilização do site
- [Python](https://www.python.org/): Back-end
- [MySQL](https://www.mysql.com/): Banco de Dados
- [JavaScript](https://www.javascript.com/): Front-end
- [Flask](https://flask.palletsprojects.com/en/2.2.x/): Integração Back-end/Front-end
- [Figma](http://www.figma.com): Prototipagem
- [Visual Studio Code](https://code.visualstudio.com/): Algoritmos
- [Discord](https://discord.com/): Comunicação
- [GitHub](https://github.com/): Versionamento e documentação

<span id="equipe">

## Equipe

|    Função    | Nome                     | LinkedIn | Github |
| :----------: | :----------------------- | -------- | ------ |
| Scrum Master | Elaine Santos | [LinkedIn](https://www.linkedin.com/in/elaineads/) | [Github](https://github.com/elaineads)
| Product Owner | Leandro Ferraz Luz | [LinkedIn](https://www.linkedin.com/in/leandro-f-luz/) | [Github](https://github.com/l3androluz)
|   Dev Team   | Jonas Ribeiro |[LinkedIn](https://www.linkedin.com/in/jonasrsribeiro/) | [Github](https://github.com/jonasrsribeiro)
|   Dev Team   | Tiago Souza | [LinkedIn](https://www.linkedin.com/in/tiagosouzadesenvolvedor) | [Github](https://github.com/Tiag-ctrl)
|   Dev Team   | Bruno Marcondes | [LinkedIn](https://www.linkedin.com/in/bruno-marcondes-cardozo-a4b374225) | [Github](https://github.com/brunom4rcondes)
|   Dev Team   | José Henninger | --- | [Github](https://github.com/HenningerJv)
