# LAB02 - Manual de execucao dos trials

Este manual deve ser lido por todos os participantes antes da Sprint 2. Ele define como preparar, executar, testar e registrar cada tentativa do experimento.

## 1. Objetivo do experimento

Cada participante resolvera os mesmos quatro katas em dois tratamentos:

- `IA`: o assistente de IA pode ser usado;
- `MANUAL`: nenhum assistente de IA pode ser consultado ou utilizado.

Cada participante fara quatro trials no total: dois com IA e dois sem IA. Cada kata sera resolvido uma unica vez por participante, de acordo com a distribuicao definida na Issue 22.

O limite de cada trial e de 35 minutos, ou 2100 segundos. O trial termina quando todos os testes passam ou quando o tempo se esgota.

## 2. Antes de comecar

Antes da execucao oficial, o grupo deve confirmar:

- [ ] Os quatro katas foram revisados por todos.
- [ ] Cada participante sabe quais katas fara com IA e quais fara IA.
- [ ] A ordem dos trials esta registrada.
- [ ] O Python e o pytest estao instalados.
- [ ] O cronometro esta pronto.
- [ ] O participante sabe onde salvar a solucao e os dados.
- [ ] O ambiente do assistente esta igual ao definido pelo grupo.
- [ ] O participante nao viu a solucao de outro participante.

A execucao oficial nao deve comecar antes de a matriz de tratamentos e a ordem estarem congeladas.

## 3. Preparar o ambiente

Na raiz do repositorio, execute:

```powershell
cd LAB02
python --version
python -m pip install -r requirements.txt
pytest --version
```

Se o `requirements.txt` ainda nao existir, a instalacao sera definida na Issue 4. Nao instale dependencias diferentes durante um trial sem registrar a mudanca.

Os testes devem ser executados com a mesma versao do Python e do pytest para todos os participantes.

## 4. Onde fica a solucao

A pasta `LAB02/katas` contem os enunciados e os testes de aceitacao. Ela nao deve ser usada para guardar varias tentativas, pois uma nova tentativa poderia sobrescrever a anterior.

Para cada trial, crie uma copia completa da pasta do kata dentro de `LAB02/trials`.

Exemplo para o participante P1, kata K1, tratamento IA:

```powershell
New-Item -ItemType Directory -Force LAB02/trials/P1 | Out-Null
Copy-Item -Recurse LAB02/katas/kata_01 LAB02/trials/P1/K1_IA
```

Exemplo para o participante P1, kata K3, tratamento MANUAL:

```powershell
Copy-Item -Recurse LAB02/katas/kata_03 LAB02/trials/P1/K3_MANUAL
```

A estrutura final de um participante sera parecida com:

```text
LAB02/trials/
└── P1/
    ├── K1_IA/
    │   ├── README.md
    │   ├── solution.py
    │   └── test_kata_01.py
    ├── K2_MANUAL/
    ├── K3_IA/
    └── K4_MANUAL/
```

A unica alteracao permitida durante o trial e no arquivo `solution.py` da copia. Nao altere os testes de aceitacao nem o enunciado.

O arquivo inicial `solution.py` contem apenas `NotImplementedError`. Substitua esse conteudo pela sua implementacao durante o trial.

## 5. Como executar um trial

Para cada tentativa, siga exatamente esta ordem:

1. Confirme o participante, kata, tratamento e ordem do trial.
2. Crie a copia da pasta do kata.
3. Abra apenas o `README.md` e o arquivo `solution.py` da copia.
4. Prepare o cronometro.
5. Inicie o cronometro e registre o horario de inicio.
6. Resolva o problema dentro do arquivo `solution.py`.
7. Execute os testes quando quiser verificar o progresso.
8. Pare o cronometro assim que todos os testes passarem.
9. Se 35 minutos forem atingidos antes do sucesso, pare imediatamente.
10. Execute os testes uma ultima vez e registre o resultado final.
11. Preencha o registro do trial.

Comando para testar K1:

```powershell
cd LAB02/trials/P1/K1_IA
pytest -q test_kata_01.py
```

Comando para testar K2:

```powershell
cd LAB02/trials/P1/K2_MANUAL
pytest -q test_kata_02.py
```

Use o nome do teste correspondente ao kata. O pytest deve mostrar a quantidade de testes aprovados e falhos.

## 6. Regras do tratamento IA

Durante um trial `IA`:

- O assistente de IA escolhido pelo grupo pode ser utilizado.
- O participante pode pedir explicacoes, exemplos, revisoes e sugestoes de codigo.
- O participante continua responsavel por executar e avaliar o codigo.
- Toda interacao relevante deve ser registrada.
- Registre o nome e a versao do assistente utilizado.
- Nao consulte a solucao de outro participante.

Registre pelo menos:

- quantidade de prompts ou interacoes;
- horario aproximado das interacoes, se possivel;
- se o codigo foi aceito integralmente, parcialmente ou apenas usado como sugestao.

Nao apague o historico de prompts antes de concluir o registro do trial.

## 7. Regras do tratamento MANUAL

Durante um trial `MANUAL`:

- Nao use GitHub Copilot, ChatGPT, Claude, Gemini ou qualquer outro assistente.
- Nao pesquise a solucao na internet.
- Nao consulte codigo de outro participante.
- Pode usar a documentacao normal da linguagem e das bibliotecas permitidas pelo grupo.
- Nao receba dicas sobre a solucao de outro participante durante o trial.

Se o participante consultar IA ou uma solucao externa por engano, o trial deve ser marcado como invalido e repetido somente se o grupo tiver definido essa regra antes da execucao. Nunca esconda o ocorrido.

## 8. O que significa passar

Um trial atingiu `time-to-green` quando todos os testes de aceitacao do kata passam no pytest.

Nao basta:

- o programa parecer correto manualmente;
- alguns testes passarem;
- a funcao funcionar somente para o exemplo do enunciado;
- alterar ou remover testes para obter sucesso.

A primeira execucao em que todos os testes passam define o `time-to-green`. O tempo deve ser registrado em segundos desde o inicio do trial.

## 9. Trial censurado

Se todos os testes nao passarem em 35 minutos:

- pare de programar imediatamente;
- execute o pytest uma ultima vez;
- registre quantos testes passaram e falharam;
- marque `censored` como `true`;
- registre `time_to_green_seconds` como vazio ou `null`;
- registre `duration_seconds` como 2100;
- nao descarte o trial da pesquisa.

O codigo parcial deve ser preservado, pois sera usado nas metricas estaticas.

## 10. Registro obrigatorio de cada trial

Crie um registro para cada tentativa com os campos abaixo:

```text
participant_id
kata_id
treatment
order
start_time
end_time
duration_seconds
time_to_green_seconds
time_box_seconds
censored
tests_total
tests_passed
tests_failed
prompts_count
python_version
pytest_version
assistant_name
assistant_version
notes
```

Exemplo de registro IA concluido:

```text
participant_id=P1
kata_id=K1
treatment=IA
order=1
start_time=2026-09-10T19:00:00-03:00
end_time=2026-09-10T19:18:42-03:00
duration_seconds=1122
time_to_green_seconds=1122
time_box_seconds=2100
censored=false
tests_total=10
tests_passed=10
tests_failed=0
prompts_count=4
python_version=3.11.x
pytest_version=8.x
assistant_name=preencher
assistant_version=preencher
notes=preencher
```

Exemplo de registro manual censurado:

```text
participant_id=P2
kata_id=K3
treatment=MANUAL
order=2
start_time=2026-09-10T20:00:00-03:00
end_time=2026-09-10T20:35:00-03:00
duration_seconds=2100
time_to_green_seconds=null
time_box_seconds=2100
censored=true
tests_total=10
tests_passed=7
tests_failed=3
prompts_count=0
python_version=3.11.x
pytest_version=8.x
assistant_name=none
assistant_version=none
notes=preencher
```

Os arquivos de dados devem ser armazenados em uma pasta de trials, sem credenciais e sem tokens. O formato CSV ou JSON final sera definido na Issue 7.

## 11. Depois de cada trial

Depois da tentativa:

1. Nao altere mais o `solution.py`.
2. Execute os testes finais.
3. Salve o registro do trial.
4. Copie ou preserve o historico de prompts quando o tratamento for IA.
5. Registre observacoes sobre dificuldades, interrupcoes ou erros.
6. Nao compare resultados com outros participantes antes de todos concluirem os trials.

As metricas estaticas serao executadas depois sobre o codigo final preservado, usando o mesmo procedimento para todos os trials.

## 12. O que nao pode ser feito

- Alterar os testes para facilitar a aprovacao.
- Compartilhar solucoes entre participantes.
- Resolver o mesmo kata mais de uma vez ate obter um resultado melhor.
- Reiniciar o cronometro sem registrar o motivo.
- Continuar programando depois dos 35 minutos.
- Trocar o tratamento no meio do trial.
- Apagar um trial que falhou.
- Colocar tokens, senhas ou conversas com dados sensiveis no repositorio.

## 13. Checklist individual

Antes de iniciar:

- [ ] Sei meu participante, kata, tratamento e ordem.
- [ ] Criei a copia correta da pasta do kata.
- [ ] O arquivo de testes nao foi alterado.
- [ ] O cronometro esta pronto.
- [ ] Sei como registrar o resultado.

Ao finalizar:

- [ ] Registrei inicio e fim.
- [ ] Registrei o primeiro momento em que todos os testes passaram, se ocorreu.
- [ ] Registrei testes totais, aprovados e falhos.
- [ ] Marquei `censored` corretamente.
- [ ] Preservei o `solution.py` final.
- [ ] Registrei prompts no tratamento IA.
- [ ] Confirmei que nao usei IA no tratamento MANUAL.
- [ ] Registrei problemas e observacoes.

## 14. Responsabilidade do grupo

Todos devem executar os trials definidos para si. A pessoa responsavel pela coleta deve conferir se existe um registro para cada combinacao de participante, kata e tratamento.

Para tres participantes e quatro katas, o resultado esperado e:

- 12 trials no total;
- 6 trials IA;
- 6 trials MANUAL;
- cada participante deve ter 2 trials IA e 2 trials MANUAL.

Antes de iniciar a Sprint 2, o grupo deve revisar a planilha ou arquivo de dados e confirmar que nenhum trial esta faltando.
