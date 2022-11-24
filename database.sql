create database flaskapp;

USE flaskapp;

CREATE TABLE gerenteAgencia (
  gerente_id INT NOT NULL AUTO_INCREMENT,
  gerente_nome VARCHAR(45) NOT NULL,
  gerente_cpf VARCHAR(11) NOT NULL,
  gerente_nasc TEXT(6) NOT NULL,
  gerente_genero VARCHAR(30) NOT NULL,
  gerente_end VARCHAR(150) NOT NULL,
  num_matricula VARCHAR(5) NOT NULL,
  num_agencia text(10) NOT NULL,
  data_criacao text(6) NOT NULL,
  num_senha VARCHAR(180) NOT NULL,
  PRIMARY KEY (gerente_id),
  UNIQUE INDEX num_matricula_UNIQUE (num_matricula ASC));
  

CREATE TABLE agencias (
  agencia_id INT PRIMARY KEY AUTO_INCREMENT,
  numero_agencia VARCHAR(20),
  numero_clientes VARCHAR(3),
  data_criacao text(6) not null,
  gerente_id int,
  foreign key(gerente_id) references gerenteAgencia (gerente_id),
  end_agencia VARCHAR (150));

CREATE TABLE gerenteGeral (
  GG_id INT NOT NULL primary key AUTO_INCREMENT,
  GG_nome VARCHAR(45) NOT NULL,
  GG_num_matricula VARCHAR(5) NOT NULL,
  GG_num_senha VARCHAR(180) NOT NULL,
  GG_primeira_vez tinyint(1) not null);
  
INSERT INTO gerenteGeral (
GG_nome,
GG_num_matricula,
GG_num_senha,
GG_primeira_vez)
VALUES ('Gerente Geral', 00001, 123, 1);

CREATE TABLE users (
  user_id INT PRIMARY KEY AUTO_INCREMENT,
  nome VARCHAR(40),
  cpf VARCHAR(11),
  dataAniversario TEXT(6),
  genero VARCHAR(30),
  endereco VARCHAR(150),
  tipoConta varchar(30) not null,
  senha VARCHAR(180),
  confirmacaoSenha VARCHAR(180),
  contaBancaria VARCHAR(9),
  agenciaBancaria VARCHAR(4),
  saldoBancario DECIMAL(19,2),
  chequeEspecial tinyint(0),
  gerente_id int,
  foreign key(gerente_id) references gerenteAgencia (gerente_id),
  UNIQUE INDEX contaBancaria_UNIQUE (contaBancaria ASC));

create table movimentacaoConta
(gasto_id int primary key auto_increment,
dataHoraMovimentacao text(40),
tipoMovimentacao text(30),
movimentacao decimal(19,2),
user_id int,
foreign key(user_id) references users(user_id));

create table gerenciamentoUsuarios
(solicitacao_id int primary key auto_increment,
dataHoraSolicitacao text(40),
tipoSolicitacao text(30),
usuarioDaSolicitacao varchar(40),
ultimaTransacao tinyint(0) not null,
user_id int,
foreign key(user_id) references users(user_id));

create table confirmacaoDeposito
(deposito_id int primary key auto_increment,
nome varchar(40),
contaBancaria varchar (9) not null,
agenciaBancaria varchar (4) not null,
saldoAtual decimal(19,2) not null,
valorDeposito decimal(19,2) not null,
saldoFinal decimal(19,2) not null,
statusSolicitacao VARCHAR(40) not null,
user_id int,
foreign key(user_id) references users (user_id),
solicitacao_id int,
foreign key(solicitacao_id) references gerenciamentoUsuarios (solicitacao_id));

create table confirmacaoAbertura
(abertura_id int primary key auto_increment,
nome VARCHAR(40) NOT NULL,
cpf VARCHAR(11) NOT NULL,
dataAniversario TEXT(6) NOT NULL,
genero VARCHAR(30) NOT NULL,
endereco VARCHAR(150) NOT NULL,
tipoConta VARCHAR(30),
contaBancaria VARCHAR(9) NOT NULL,
agenciaBancaria VARCHAR(4) NOT NULL,
statusSolicitacao VARCHAR(40) not null,
user_id int,
foreign key(user_id) references users (user_id),
solicitacao_id int,
foreign key(solicitacao_id) references gerenciamentoUsuarios (solicitacao_id));

create table confirmacaoFechamento
(fechamento_id int primary key auto_increment,
nome VARCHAR(40) NOT NULL,
cpf VARCHAR(11) NOT NULL,
dataAniversario TEXT(6) NOT NULL,
genero VARCHAR(30) NOT NULL,
endereco VARCHAR(150) NOT NULL,
tipoConta VARCHAR(30),
contaBancaria VARCHAR(9) NOT NULL,
agenciaBancaria VARCHAR(4) NOT NULL,
statusSolicitacao VARCHAR(40) not null,
user_id int,
foreign key(user_id) references users (user_id),
solicitacao_id int,
foreign key(solicitacao_id) references gerenciamentoUsuarios (solicitacao_id));

create table confirmacaoAlteracao
(alteracao_id int primary key auto_increment,
nome VARCHAR(40) NOT NULL,
cpf VARCHAR(11) NOT NULL,
dataAniversario TEXT(6) NOT NULL,
genero VARCHAR(30) NOT NULL,
endereco VARCHAR(150) NOT NULL,
senha VARCHAR(180) NOT NULL,
confirmacaoSenha VARCHAR(180) NOT NULL,
statusSolicitacao VARCHAR(40) not null,
user_id int,
foreign key(user_id) references users (user_id),
solicitacao_id int,
foreign key(solicitacao_id) references gerenciamentoUsuarios (solicitacao_id));

create table configBanco(
config_id int primary key auto_increment,
dataInicializacao text(15),
dataCorrente text(15),
capitalTotal decimal(19,2) not null,
taxaJurosPoupanca decimal(4,4) not null,
taxaJurosCheque decimal(4,4) not null);

create table poupanca(
poupanca_id int primary key auto_increment,
valorInicial decimal(19,2) not null,
dataInicial text(15),
dataProximoMes text(15),
valorTaxa decimal(4,4),
valorAtualizado decimal(19,2) not null,
user_id int,
foreign key(user_id) references users (user_id),
config_id int,
foreign key(config_id) references configBanco (config_id));

create table chequeEspecial(
valorNegativo decimal(19,2) not null,
dataInicial text(15),
dataFinal text(15),
valorTaxa decimal(4,4),
valorAtualizado decimal(19,2),
user_id int,
foreign key(user_id) references users (user_id));


USE flaskapp;
select * from users;
select * from movimentacaoConta;
select * from gerenciamentoUsuarios;
select * from confirmacaoDeposito;
select * from confirmacaoAlteracao;
select * from confirmacaoAbertura;
select * from confirmacaoFechamento;

select * from gerenteAgencia;
select * from gerenteGeral;
select * from agencias;
select * from poupanca;
select * from configBanco;
select * from chequeEspecial;

SELECT g.dataHoraSolicitacao, g.tipoSolicitacao, g.usuarioDaSolicitacao, g.solicitacao_id FROM gerenciamentoUsuarios g, users u WHERE u.gerente_id = "1" and u.user_id = g.user_id;

SELECT g.dataHoraSolicitacao, g.tipoSolicitacao, g.usuarioDaSolicitacao, g.solicitacao_id FROM gerenciamentoUsuarios g, users u WHERE u.gerente_id = "1" and u.user_id = g.user_id ORDER BY g.solicitacao_id DESC;






drop table agencias;
drop table gerenteGeral;
drop table gerenteAgencia;
drop table confirmacaoAbertura;
drop table confirmacaoDeposito;
drop table gerenciamentoUsuarios;
drop table movimentacaoConta;
drop table confirmacaoAlteracao;
drop table users;
drop table confirmacaoAlteracao;
drop table gerenteGeral;
drop table configBanco;
drop table poupanca;
drop table agencias;
drop table chequeEspecial;





drop database flaskapp;
