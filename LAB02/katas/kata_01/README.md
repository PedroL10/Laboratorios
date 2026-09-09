# K1 - Resumo de leituras

**Nivel:** Facil

Implemente `summarize_readings(readings, minimum)` em `solution.py`.

A funcao recebe uma lista de numeros inteiros representando leituras de um sensor e um limite minimo. Ela deve retornar um dicionario com:

- `count`: quantidade de leituras maiores ou iguais a `minimum`;
- `average`: media de todas as leituras, arredondada para duas casas decimais;
- `maximum`: maior leitura, ou `None` quando a lista estiver vazia.

Regras:

- A lista pode estar vazia.
- Leituras podem ser negativas.
- O limite deve ser aplicado com `>=`.
- Nao altere a lista recebida.
- Nao use bibliotecas externas.

Exemplo:

```python
summarize_readings([10, 12, 8, 12], 10)
# {'count': 3, 'average': 10.5, 'maximum': 12}
```

Execute os testes com:

```powershell
pytest -q
```
