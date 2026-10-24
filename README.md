# Observatório Eleitoral PE

Painel de desempenho eleitoral em Pernambuco nas eleições de 2022 e 2026: deputado federal, deputado estadual, senador, governador e presidente, por candidato, partido, federação, região e município, com simulador de cadeiras.

O site é uma única página (`index.html`) com os dados embutidos; não há servidor nem banco de dados. Pode ser instalado como aplicativo no Windows pelo Edge ou pelo Chrome (ícone "Instalar aplicativo" na barra de endereço) e funciona sem internet depois de instalado.

## Fontes

Tribunal Superior Eleitoral, Portal de Dados Abertos (licença CC BY):

- 2026: votação por município e por seção, e totais da totalização.
- 2022: votação por seção (UF PE), votação nominal por município e zona (arquivos PE e BR) e detalhe da apuração por município e zona (arquivo BR).

O cálculo de cadeiras segue os arts. 106 a 109 do Código Eleitoral (Lei 14.211/2021), com federação contada como um partido, e reproduz os eleitos oficiais de 2022 e 2026.

## Como atualizar

Os scripts em `fonte/` geram a base e a página:

1. `prep.py`, `prep_maj.py`, `prep_maj22.py` e `prep_pres22.py` montam `dados.json` a partir dos arquivos do TSE.
2. `test_seats.js` confere o cálculo de cadeiras contra os eleitos oficiais.
3. `build_site.py` gera `index.html`, `manifest.webmanifest` e `sw.js` a partir de `template.html` e `seats.js`.
