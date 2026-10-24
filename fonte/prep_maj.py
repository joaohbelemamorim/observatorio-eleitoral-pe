"""Acrescenta presidente, governador e senador (2026, 1º turno) à base do painel."""
import json, sys, glob
import pandas as pd

A, MAJ, PRES, BASE = sys.argv[1:5]
d = json.load(open(BASE, encoding="utf-8"))
reg = pd.read_csv(glob.glob(A + "/*regioes_pe.csv")[0], sep=";", dtype=str)
reg["cod_tse"] = reg.cod_tse.astype(int)
reg = reg.sort_values("municipio").reset_index(drop=True)
mun_idx = {c: i for i, c in enumerate(reg.cod_tse)}
assert [m[0] for m in d["municipios"]] == list(reg.municipio)
tot = pd.read_csv(glob.glob(A + "/*totais_municipio_2026.csv")[0], sep=";")
eleitorado = tot[tot.cargo == "Deputado Federal"].set_index("cod_tse").eleitorado

pres = pd.read_csv(PRES, sep=";", dtype=str)
NOMES = {
    "PR": {r.numero: (r.nome_urna, r.partido) for r in pres.itertuples()},
    "GOV": {"14": ("RENAN HALLAIS", "MISSÃO"), "16": ("GUILHERME FONSECA", "PSTU"), "29": ("VICTOR ASSIS", "PCO"),
            "35": ("PROFESSOR JEREMIAS", "DEMOCRATA"), "40": ("JOÃO CAMPOS", "PSB"), "50": ("IVAN MORAES", "PSOL"),
            "55": ("RAQUEL LYRA", "PSD"), "80": ("PROFESSORA CAMILA", "UP")},
    "SEN": {"111": ("EDUARDO DA FONTE", "PP"), "123": ("MARÍLIA ARRAES", "PDT"), "130": ("HUMBERTO COSTA", "PT"),
            "161": ("MARIANO MACEDO", "PSTU"), "180": ("PAULO RUBEM SANTIAGO", "REDE"), "222": ("MENDONÇA FILHO", "PL"),
            "290": ("MAILSON DA SILVA NETO", "PCO"), "300": ("CARLOS SANT'ANNA", "NOVO"), "355": ("PASTOR GILVAN COSTA", "DEMOCRATA"),
            "555": ("TÚLIO GADÊLHA", "PSD"), "800": ("SAMUEL TIMOTEO", "UP"), "801": ("GORETT BITU", "UP")},
}
SITU = {"PR": {"13": "2º turno", "22": "2º turno"}, "GOV": {"55": "Eleito"}, "SEN": {"130": "Eleito", "123": "Eleito"}}
CARGO = {"PR": 1, "GOV": 3, "SEN": 5}

x = pd.read_pickle(MAJ)
x["mi"] = x.mun.map(mun_idx)
assert x.mi.notna().all()
for sig, cod in CARGO.items():
    y = x[x.cargo == cod]
    nom = y[y.tipo_voto == "nominal"]
    nums = sorted(nom.numero.unique(), key=lambda n: -nom[nom.numero == n].votos.sum())
    cands, votos = [], []
    for n in nums:
        nome, partido = NOMES[sig].get(n, (f"CANDIDATO {n} (registro não deferido)", "?"))
        anul = 0 if n in NOMES[sig] else 1
        cands.append([n, nome, partido, SITU[sig].get(n, "Não eleito"), "s" if SITU[sig].get(n) == "Eleito" else "", anul])
        g = nom[nom.numero == n].groupby("mi").votos.sum()
        flat = []
        for mi, v in g.items():
            if v > 0: flat += [int(mi), int(v)]
        votos.append(flat)
    # comparecimento: uma vez por seção
    comp = y.drop_duplicates(["mun", "zona", "secao"]).groupby("mi").comparecimento_cargo.sum()
    br = y[y.tipo_voto == "branco"].groupby("mi").votos.sum()
    nu = y[y.tipo_voto == "nulo"].groupby("mi").votos.sum()
    n = len(d["municipios"])
    el = [int(eleitorado[c]) for c in reg.cod_tse]
    partidos = sorted({c[2] for c in cands})
    d["anos"]["2026"][sig] = {
        "candidatos": cands, "votos": votos,
        "partidos": {p: {"fed": "", "leg": [], "anulado": 0} for p in partidos},
        "totais": {"eleitorado": el,
                   "comparecimento": [int(comp.get(i, 0)) for i in range(n)],
                   "brancos": [int(br.get(i, 0)) for i in range(n)],
                   "nulos": [int(nu.get(i, 0)) for i in range(n)]},
    }
    print(sig, len(cands), "nominal", int(nom.votos.sum()), "comp", int(comp.sum()), [c[1] for c in cands if c[5]])
json.dump(d, open(BASE, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
