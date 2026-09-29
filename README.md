# Radar de Performance · SP

Dashboard `index.html` **"Nodos com descarte"**: top ofensores de _Excede la capacidad_ e volume
de descarte entre os Facility Nodos da carteira que **não operam aos sábados** (coluna
`SÁBADO = "-"`), incluindo os que abrem **de segunda a sexta, sem fim de semana, com alto
volume** (média diária ≥ mediana da base), com base em 2026.

Abra `index.html` no navegador (arquivo único, funciona offline; os dados ficam embutidos nele).

## Atualizar os dados

```bash
pip install pandas openpyxl
python3 scripts/gerar_dados.py caminho/general.xlsx caminho/Carteira.xlsx 2026
```
