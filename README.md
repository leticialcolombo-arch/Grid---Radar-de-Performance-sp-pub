# Radar de Performance · SP

Dashboard `index.html`: **top ofensores de _Excede la capacidad_** entre os Facility Nodos
da carteira que **não operam aos sábados** (coluna `SÁBADO = "-"` na Carteira), com base em 2026.

Abra `index.html` no navegador (funciona offline; os dados ficam em `dados.js`).

## Atualizar os dados

```bash
pip install pandas openpyxl
python3 scripts/gerar_dados.py caminho/general.xlsx caminho/Carteira.xlsx 2026
```
