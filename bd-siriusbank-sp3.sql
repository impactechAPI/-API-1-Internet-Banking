create database flaskapp;
use flaskapp;

CREATE TABLE `flaskapp`.`users` (
  `user_id` INT NOT NULL AUTO_INCREMENT,
  `nome` VARCHAR(40) NOT NULL,
  `cpf` VARCHAR(11) NOT NULL,
  `dataAniversario` TEXT(6) NOT NULL,
  `genero` VARCHAR(30) NOT NULL,
  `endereco` VARCHAR(150) NOT NULL,
  `senha` VARCHAR(180) NOT NULL,
  `confirmacaoSenha` VARCHAR(180) NOT NULL,
  `contaBancaria` VARCHAR(9) NULL,
  `agenciaBancaria` VARCHAR(4) NULL,
  `saldoBancario` DECIMAL(19,2) NULL,
  PRIMARY KEY (`user_id`),
  UNIQUE INDEX `contaBancaria_UNIQUE` (`contaBancaria` ASC) VISIBLE);

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
contaBancaria VARCHAR(9) NULL,
agenciaBancaria VARCHAR(4) NULL,
statusSolicitacao text(20) not null,
user_id int,
foreign key(user_id) references users (user_id),
solicitacao_id int,
foreign key(solicitacao_id) references gerenciamentoUsuarios (solicitacao_id));

CREATE TABLE gerenteAgencia (
  gerente_id INT NOT NULL AUTO_INCREMENT,
  gerente_nome VARCHAR(45) NOT NULL,
  num_matricula VARCHAR(5) NOT NULL,
  num_agencia text(10) NOT NULL,
  num_senha VARCHAR(180) NOT NULL,
  PRIMARY KEY (gerente_id),
  UNIQUE INDEX num_matricula_UNIQUE (num_matricula ASC));
  
INSERT INTO gerenteAgencia (
gerente_id,
gerente_nome,
num_matricula,
num_agencia,
num_senha)
VALUES (4,'Gerente Agencia 2', 33333, '0001', 123);

CREATE TABLE gerenteGeral (
  GG_id INT NOT NULL primary key AUTO_INCREMENT,
  GG_nome VARCHAR(45) NOT NULL,
  GG_num_matricula VARCHAR(5) NOT NULL,
  GG_num_senha VARCHAR(180) NOT NULL);
  
INSERT INTO gerenteGeral (
GG_nome,
GG_num_matricula,
GG_num_senha)
VALUES ('Gerente Geral', 00001, 123);

create table listaAgencias (
id_numAgencia int not null primary key auto_increment,
numAgencia text(4) not null);


select * from users;
select * from movimentacaoConta;
select * from gerenciamentoUsuarios;
select * from confirmacaoDeposito;
select * from confirmacaoAbertura;
select * from gerenteAgencia;
select * from gerenteGeral;
select * from listaAgencias;
