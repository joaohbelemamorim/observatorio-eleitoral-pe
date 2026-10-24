// Distribuição de cadeiras no sistema proporcional (Código Eleitoral, arts. 106 a 109,
// com a redação da Lei 14.211/2021 e o entendimento do STF nas ADIs 7228, 7263 e 7325).
// Federação partidária conta como um único partido.
//
// unidades: [{id, votos, cands:[{id, votos}]}]  (votos = nominais válidos + legenda)
// validos:  total de votos válidos da eleição
// vagas:    número de cadeiras
function distribuirCadeiras(unidades, validos, vagas) {
  const qe = arredondaQE(validos / vagas);
  const U = unidades.map(u => ({
    id: u.id, votos: u.votos,
    cands: [...u.cands].sort((a, b) => b.votos - a.votos),
    qp: Math.floor(u.votos / qe), porQP: 0, porMedia: 0, eleitos: [], prox: 0,
  }));
  const eleitos = [];
  // 1ª etapa: quociente partidário, candidatos com pelo menos 10% do QE
  for (const u of U) {
    while (u.porQP < u.qp && u.prox < u.cands.length && u.cands[u.prox].votos >= 0.1 * qe) {
      const c = u.cands[u.prox++];
      u.porQP++; u.eleitos.push(c.id);
      eleitos.push({ id: c.id, unidade: u.id, via: 'QP' });
    }
  }
  let restantes = vagas - eleitos.length;
  const total = u => u.porQP + u.porMedia;
  // 2ª etapa: sobras para quem tem 80% do QE, com candidato de pelo menos 20% do QE
  while (restantes > 0) {
    let melhor = null, melhorMedia = -1;
    for (const u of U) {
      if (u.votos < 0.8 * qe) continue;
      if (!(u.prox < u.cands.length && u.cands[u.prox].votos >= 0.2 * qe)) continue;
      const m = u.votos / (total(u) + 1);
      if (m > melhorMedia) { melhorMedia = m; melhor = u; }
    }
    if (!melhor) break;
    const c = melhor.cands[melhor.prox++];
    melhor.porMedia++; melhor.eleitos.push(c.id);
    eleitos.push({ id: c.id, unidade: melhor.id, via: 'média' }); restantes--;
  }
  // 3ª etapa: cadeiras que sobraram vão por média a todos os partidos, sem exigência de votação mínima
  while (restantes > 0) {
    let melhor = null, melhorMedia = -1;
    for (const u of U) {
      if (u.prox >= u.cands.length) continue;
      const m = u.votos / (total(u) + 1);
      if (m > melhorMedia) { melhorMedia = m; melhor = u; }
    }
    if (!melhor) break;
    const c = melhor.cands[melhor.prox++];
    melhor.porMedia++; melhor.eleitos.push(c.id);
    eleitos.push({ id: c.id, unidade: melhor.id, via: 'média (3ª fase)' }); restantes--;
  }
  return {
    qe,
    unidades: U.map(u => ({ id: u.id, votos: u.votos, qp: u.qp, porQP: u.porQP, porMedia: u.porMedia,
      cadeiras: total(u), pctQE: u.votos / qe, eleitos: u.eleitos })),
    eleitos,
  };
}
// Fração igual ou inferior a meio é desprezada; superior a meio, arredonda para cima (art. 106).
function arredondaQE(x) { const f = x - Math.floor(x); return f > 0.5 ? Math.ceil(x) : Math.floor(x); }
if (typeof module !== 'undefined') module.exports = { distribuirCadeiras };
