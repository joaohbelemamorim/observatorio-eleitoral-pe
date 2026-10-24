"""Acrescenta governador (1º e 2º turno) e senador de 2022 à base do painel, a partir do arquivo de seções do TSE."""
import json, sys
import pandas as pd

MAJ, BASE = sys.argv[1:3]
d = json.load(open(BASE, encoding="utf-8"))
PART = {"77": "SOLIDARIEDADE", "45": "PSDB", "22": "PL", "40": "PSB", "44": "UNIÃO", "21": "PCB", "50": "PSOL", "14": "PTB",
        "35": "PMB", "16": "PSTU", "29": "PCO", "13": "PT", "55": "PSD", "28": "PRTB"}
# nomes de urna conhecidos, para comparar candidatos entre 2022 e 2026
URNA = {"MARÍLIA VALENÇA ROCHA ARRAES DE ALENCAR": "MARÍLIA ARRAES", "RAQUEL TEIXEIRA LYRA LUCENA": "RAQUEL LYRA",
        "ANDERSON FERREIRA RODRIGUES": "ANDERSON FERREIRA", "DANILO JORGE DE BARROS CABRAL": "DANILO CABRAL",
        "MIGUEL DE SOUZA LEÃO COELHO": "MIGUEL COELHO", "MARIA TERESA LEITÃO DE MELO": "TERESA LEITÃO",
        "GILSON MACHADO GUIMARÃES NETO": "GILSON MACHADO", "ANDRÉ CARLOS ALVES DE PAULA FILHO": "ANDRÉ DE PAULA"}
SITU = {"GOV": {"77": "2º turno", "45": "2º turno"}, "GOV2": {"45": "Eleito"}, "SEN": {"130": "Eleito"}}
x = pd.read_pickle(MAJ)
MZ = pd.read_pickle(sys.argv[4])
# índice de municípios: mesmo código TSE usado na base (ordem alfabética do arquivo de regiões)
import glob
reg = pd.read_csv(glob.glob(sys.argv[3] + "/*regioes_pe.csv")[0], sep=";", dtype=str)
reg["cod_tse"] = reg.cod_tse.astype(int)
reg = reg.sort_values("municipio").reset_index(drop=True)
mun_idx = {c: i for i, c in enumerate(reg.cod_tse)}
x["mi"] = x.CD_MUNICIPIO.map(mun_idx)
assert x.mi.notna().all()
n = len(d["municipios"])
for sig, turno, cargo in [("GOV", 1, 3), ("GOV2", 2, 3), ("SEN", 1, 5)]:
    y = x[(x.NR_TURNO == turno) & (x.CD_CARGO == cargo)]
    nom = y[~y.NR_VOTAVEL.isin(["95", "96"])]
    tot = nom.groupby(["NR_VOTAVEL", "NM_VOTAVEL"]).QT_VOTOS.sum().sort_values(ascending=False)
    cands, votos = [], []
    of = MZ[(MZ.CD_CARGO == cargo) & (MZ.NR_TURNO == turno)].groupby("NR_CANDIDATO").agg(
        urna=("NM_URNA_CANDIDATO", "first"), dest=("NM_TIPO_DESTINACAO_VOTOS", "first"))
    for (num, nome), _ in tot.items():
        sit = SITU[sig].get(num, "Não eleito")
        urna = of.urna.get(num, URNA.get(nome, nome))
        anul = 0 if of.dest.get(num) == "Válido" else 1  # ausente do arquivo oficial ou com votos anulados
        cands.append([num, urna, PART[num[:2]], sit, "s" if sit == "Eleito" else "", anul])
        g = nom[nom.NR_VOTAVEL == num].groupby("mi").QT_VOTOS.sum()
        flat = []
        for mi, v in g.items():
            if v > 0: flat += [int(mi), int(v)]
        votos.append(flat)
    comp = y.groupby("mi").QT_VOTOS.sum()
    if cargo == 5:  # um voto por eleitor em 2022 (uma vaga)
        pass
    br = y[y.NR_VOTAVEL == "95"].groupby("mi").QT_VOTOS.sum()
    nu = y[y.NR_VOTAVEL == "96"].groupby("mi").QT_VOTOS.sum()
    d["anos"]["2022"][sig] = {
        "candidatos": cands, "votos": votos,
        "partidos": {p: {"fed": "", "leg": [], "anulado": 0} for p in sorted({c[2] for c in cands})},
        "totais": {"eleitorado": [None] * n, "comparecimento": [int(comp.get(i, 0)) for i in range(n)],
                   "brancos": [int(br.get(i, 0)) for i in range(n)], "nulos": [int(nu.get(i, 0)) for i in range(n)]},
    }
    print(sig, [(c[1], c[2], c[3]) for c in cands[:3]], int(comp.sum()))
json.dump(d, open(BASE, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
