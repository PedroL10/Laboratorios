# K3 - Janela de entregas

**Nivel:** Medio

Implemente `delivery_windows(deliveries)` em `solution.py`.

Cada entrega e representada por um dicionario com `start`, `end` e `zone`. Os horarios sao inteiros. A funcao deve agrupar entregas por zona e retornar, para cada zona, a quantidade de janelas de atendimento necessarias.

Duas entregas da mesma zona podem compartilhar a mesma janela quando a proxima comeca em horario maior ou igual ao fim da anterior. Quando existe sobreposicao, e necessaria uma nova janela.

Retorne um dicionario ordenado pelas chaves em ordem alfabetica, com a zona e sua quantidade maxima de janelas simultaneas. Cada entrega deve satisfazer `start < end`.

Regras:

- Uma lista vazia retorna `{}`.
- Entregas de zonas diferentes nao interferem umas nas outras.
- Entregas com `start == end` sao invalidas.
- Nao altere a lista original.
- Nao use bibliotecas externas.

Exemplo:

```python
delivery_windows([
    {"start": 1, "end": 4, "zone": "sul"},
    {"start": 2, "end": 3, "zone": "sul"},
    {"start": 4, "end": 6, "zone": "sul"},
])
# {"sul": 2}
```

Execute os testes com:

```powershell
pytest -q
```
