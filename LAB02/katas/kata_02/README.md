# K2 - Validador de etiquetas

**Nivel:** Facil

Implemente `validate_tags(text)` em `solution.py`.

A funcao recebe uma string contendo texto e etiquetas delimitadas por colchetes. As etiquetas validas sao `[nome]` e `[/nome]`. Retorne `True` somente quando todas as etiquetas estiverem corretamente aninhadas e fechadas.

Regras:

- Os nomes contem apenas letras minusculas, de `a` a `z`, e hifens.
- Etiquetas de abertura e fechamento devem ter o mesmo nome.
- O texto fora das etiquetas pode conter qualquer caractere, exceto colchetes soltos.
- Etiquetas nao podem ser auto-fechadas.
- Uma string vazia e valida.
- Nao use bibliotecas externas.

Exemplos:

```python
validate_tags("[card]texto[/card]")  # True
validate_tags("[a][b]x[/b][/a]")      # True
validate_tags("[a][b][/a][/b]")       # False
```

Execute os testes com:

```powershell
pytest -q
```
