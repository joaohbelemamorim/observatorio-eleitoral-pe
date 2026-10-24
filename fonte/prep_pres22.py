"""Acrescenta presidente 2022 (1º e 2º turno, Pernambuco) à base do painel.
Fonte: TSE, votacao_candidato_munzona_2022_BR.csv e detalhe_votacao_munzona_2022_BR.csv, filtrados para PE."""
import json, sys, glob
import pandas as pd

P, BASE, A = sys.argv[1:4]
raw = json.load(open(P, encoding="utf-8"))
d = json.load(open(BASE, encoding="utf-8"))
reg = pd.read_csv(glob.glob(A + "/*regioes_pe.csv")[0], sep=";", dtype=str)
reg["cod_tse"] = reg.cod_tse.astype(int)
reg = reg.sort_values("municipio").reset_index(drop=True)
mun_idx = {c: i for i, c in enumerate(reg.cod_tse)}
n = len(mun_idx)
SIT = {"2º TURNO": "2º turno", "ELEITO": "Eleito", "NÃO ELEITO": "Não eleito"}
rows = [r.split(",") for r in raw["rows"].split(";")]
det = [r.split(",") for r in raw["det"].split(";")]
for turno, sig in [("1", "PR"), ("2", "PR2")]:
    votos = {}
    for t, m, num, v in rows:
        if t != turno or int(v) == 0: continue
        votos.setdefault(num, {})
        mi = mun_idx[int(m)]
        votos[num][mi] = votos[num].get(mi, 0) + int(v)
    nums = sorted(votos, key=lambda k: -sum(votos[k].values()))
    cands, vl = [], []
    for num in nums:
        nome, part, sit, dest = raw["cand"][turno + "|" + num]
        s = SIT.get(sit, sit.capitalize())
        cands.append([num, nome, part, s, "s" if s == "Eleito" else "", 0 if dest == "Válido" else 1])
        flat = []
        for mi in sorted(votos[num]): flat += [mi, votos[num][mi]]
        vl.append(flat)
    tot = {k: [0] * n for k in ["eleitorado", "comparecimento", "brancos", "nulos"]}
    for t, m, apt, comp, br, nu, val in det:
        if t != turno: continue
        mi = mun_idx[int(m)]
        tot["eleitorado"][mi] += int(apt); tot["comparecimento"][mi] += int(comp)
        tot["brancos"][mi] += int(br); tot["nulos"][mi] += int(nu)
    d["anos"]["2022"][sig] = {"candidatos": cands, "votos": vl,
                              "partidos": {p: {"fed": "", "leg": [], "anulado": 0} for p in sorted({c[2] for c in cands})},
                              "totais": tot}
    tv = sum(sum(v.values()) for v in votos.values())
    print(sig, [(c[1], round(sum(votos[c[0]].values()) / tv * 100, 2)) for c in cands[:3]], "comp", sum(tot["comparecimento"]))
json.dump(d, open(BASE, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
