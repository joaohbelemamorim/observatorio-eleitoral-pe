"""Prepara a base do painel eleitoral PE (2022 e 2026) a partir dos arquivos do TSE já tratados."""
import json, sys
import pandas as pd

A = sys.argv[1]  # pasta dos anexos
S22 = sys.argv[2]  # pickle das seções 2022
OUT = sys.argv[3]
MZ = pd.read_pickle(sys.argv[4])

def f(name):
    import glob
    return glob.glob(A + "/*" + name)[0]

# Votos anulados na totalização oficial de 2026 (candidaturas indeferidas / DRAP indeferido).
# Identificados porque reproduzem exatamente, município a município, a diferença entre a soma
# nominal e os votos nominais válidos oficiais (totais_municipio_2026.csv).
ANUL = {(2026, "Deputado Federal"): {"4033", "4514", "2929"},
        (2026, "Deputado Estadual"): {"30567", "29999"}}
ANUL_PART = {(2026, "Deputado Estadual"): {"MOBILIZA"}}

CARGOS = {"Deputado Federal": "DF", "Deputado Estadual": "DE"}

# ---------- municípios ----------
reg = pd.read_csv(f("regioes_pe.csv"), sep=";", dtype=str)
reg["cod_tse"] = reg.cod_tse.astype(int)
reg = reg.sort_values("municipio").reset_index(drop=True)
mun_idx = {c: i for i, c in enumerate(reg.cod_tse)}
municipios = [[r.municipio, r.regiao, r.mesorregiao_ibge, r.cod_ibge] for r in reg.itertuples()]

# ---------- 2026 ----------
cand = pd.read_csv(f("candidatos_2026.csv"), sep=";", dtype=str)
cand["federacao"] = cand.federacao.fillna("")
cand["votos"] = cand.votos.astype(int)
vm = pd.read_csv(f("votos_municipio_2026.csv"), sep=";", dtype={"numero": str})
pm = pd.read_csv(f("partidos_municipio_2026.csv"), sep=";", dtype=str)
pm[["votos_nominais", "votos_legenda"]] = pm[["votos_nominais", "votos_legenda"]].astype(int)
pm["cod_tse"] = pm.cod_tse.astype(int)
tot = pd.read_csv(f("totais_municipio_2026.csv"), sep=";")

# partido -> número e federação (2026)
p26 = pm[["partido", "numero_partido", "federacao"]].drop_duplicates()
p26["federacao"] = p26.federacao.fillna("")

# ---------- 2022 ----------
PART22 = {"10": "REPUBLICANOS", "11": "PP", "12": "PDT", "13": "PT", "14": "PTB", "15": "MDB", "16": "PSTU",
          "18": "REDE", "19": "PODE", "20": "PSC", "21": "PCB", "22": "PL", "23": "CIDADANIA", "27": "DC",
          "28": "PRTB", "29": "PCO", "30": "NOVO", "33": "PMN", "35": "PMB", "36": "AGIR", "40": "PSB",
          "43": "PV", "44": "UNIÃO", "45": "PSDB", "50": "PSOL", "51": "PATRIOTA", "55": "PSD",
          "65": "PCDOB", "70": "AVANTE", "77": "SOLIDARIEDADE", "80": "UP", "90": "PROS"}
FED22 = {"PT": "PCDOB / PT / PV", "PCDOB": "PCDOB / PT / PV", "PV": "PCDOB / PT / PV",
         "PSDB": "CIDADANIA / PSDB", "CIDADANIA": "CIDADANIA / PSDB", "PSOL": "PSOL / REDE", "REDE": "PSOL / REDE"}

s = pd.read_pickle(S22)
s["cargo"] = s.cargo.map({6: "Deputado Federal", 7: "Deputado Estadual"})
s["cod_tse"] = s.cd_municipio.astype(int)
s["num2"] = s.numero.str[:2]

out = {"municipios": municipios, "anos": {}}

def bloco(ano, cargo, cands, votos_mun, legenda_mun, totais_mun):
    """cands: DataFrame numero,nome,partido,federacao,situacao,eleito
       votos_mun: DataFrame numero,cod_tse,votos
       legenda_mun: DataFrame partido,cod_tse,votos
       totais_mun: DataFrame cod_tse, eleitorado, comparecimento, brancos, nulos"""
    cands = cands.sort_values("numero").reset_index(drop=True)
    cidx = {n: i for i, n in enumerate(cands.numero)}
    vm = votos_mun[votos_mun.numero.isin(cidx)].copy()
    vm["ci"] = vm.numero.map(cidx)
    vm["mi"] = vm.cod_tse.map(mun_idx)
    assert vm.mi.notna().all(), "município sem índice"
    vm = vm[vm.votos > 0]
    # votos por candidato: lista plana [mi, votos, mi, votos...]
    vlist = [[] for _ in range(len(cands))]
    for ci, mi, v in zip(vm.ci, vm.mi.astype(int), vm.votos):
        vlist[ci] += [mi, int(v)]
    partidos = sorted(set(cands.partido) | set(legenda_mun.partido))
    lm = legenda_mun.copy()
    lm["mi"] = lm.cod_tse.map(mun_idx).astype(int)
    leg = {p: [] for p in partidos}
    for p, mi, v in zip(lm.partido, lm.mi, lm.votos):
        if v > 0:
            leg[p] += [int(mi), int(v)]
    tm = totais_mun.copy()
    tm["mi"] = tm.cod_tse.map(mun_idx).astype(int)
    tm = tm.sort_values("mi")
    assert len(tm) == len(municipios)
    fed = {}
    for r in cands.itertuples():
        fed[r.partido] = r.federacao
    for p in partidos:
        fed.setdefault(p, "")
    return {
        "candidatos": [[r.numero, r.nome, r.partido, r.situacao, r.eleito,
                        1 if (r.numero in ANUL.get((ano, cargo), ()) or r.partido in ANUL_PART.get((ano, cargo), ())) else 0]
                       for r in cands.itertuples()],
        "votos": vlist,
        "partidos": {p: {"fed": fed[p], "leg": leg[p], "anulado": 1 if p in ANUL_PART.get((ano, cargo), ()) else 0}
                     for p in partidos},
        "totais": {k: [int(x) if pd.notna(x) else None for x in tm[k]] for k in
                   ["eleitorado", "comparecimento", "brancos", "nulos"]},
    }

# 2026
out["anos"]["2026"] = {}
vm["cod_tse"] = vm.cod_tse.astype(int)
for cargo, sig in CARGOS.items():
    c = cand[cand.cargo == cargo].rename(columns={"nome_urna": "nome"})
    c = c[["numero", "nome", "partido", "federacao", "situacao", "eleito"]]
    v = vm[vm.cargo == cargo][["numero", "cod_tse", "votos"]]
    l = pm[pm.cargo == cargo][["partido", "cod_tse", "votos_legenda"]].rename(columns={"votos_legenda": "votos"})
    t = tot[tot.cargo == cargo][["cod_tse", "eleitorado", "comparecimento", "brancos", "nulos"]]
    out["anos"]["2026"][sig] = bloco(2026, cargo, c, v, l, t)

# 2022
out["anos"]["2022"] = {}
for cargo, sig in CARGOS.items():
    x = s[s.cargo == cargo]
    nom = x[x.numero.str.len() >= 4]
    nom_tot = nom.groupby(["numero"]).agg(nome=("nome", "first"), votos=("votos", "sum")).reset_index()
    nom_tot["partido"] = nom_tot.numero.str[:2].map(PART22)
    assert nom_tot.partido.notna().all(), nom_tot[nom_tot.partido.isna()]
    nom_tot["federacao"] = nom_tot.partido.map(FED22).fillna("")
    # situação oficial, nome de urna e votos anulados (votacao_candidato_munzona_2022_PE.csv)
    of = MZ[(MZ.DS_CARGO == cargo) & (MZ.NR_TURNO == 1)].groupby("NR_CANDIDATO").agg(
        urna=("NM_URNA_CANDIDATO", "first"), sit=("DS_SIT_TOT_TURNO", "first"), dest=("NM_TIPO_DESTINACAO_VOTOS", "first"))
    nom_tot = nom_tot.join(of, on="numero")
    nom_tot["nome"] = nom_tot.urna.fillna(nom_tot.nome)
    nom_tot["situacao"] = nom_tot.sit.fillna("Não eleito").str.capitalize().str.replace("Qp", "QP").str.replace("média", "média")
    nom_tot["eleito"] = nom_tot.sit.fillna("").str.startswith("ELEITO").map({True: "s", False: ""})
    ANUL[(2022, cargo)] = set(nom_tot[(nom_tot.dest != "Válido")].numero)
    v = nom.groupby(["numero", "cod_tse"]).votos.sum().reset_index()
    leg = x[(x.numero.str.len() == 2) & ~x.numero.isin(["95", "96"])].copy()
    leg["partido"] = leg.numero.map(PART22)
    l = leg.groupby(["partido", "cod_tse"]).votos.sum().reset_index()
    t = x.groupby("cod_tse").agg(comparecimento=("votos", "sum")).reset_index()
    br = x[x.numero == "95"].groupby("cod_tse").votos.sum().rename("brancos")
    nu = x[x.numero == "96"].groupby("cod_tse").votos.sum().rename("nulos")
    t = t.set_index("cod_tse").join(br).join(nu).fillna(0).reset_index()
    t["eleitorado"] = None
    # municípios sem linhas (não deve ocorrer)
    missing = set(mun_idx) - set(t.cod_tse)
    assert not missing, missing
    out["anos"]["2022"][sig] = bloco(2022, cargo, nom_tot, v, l, t)

json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
print("ok", OUT)
