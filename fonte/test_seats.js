const fs = require('fs');
const { distribuirCadeiras } = require('./seats.js');
const D = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
const VAGAS = { DF: 25, DE: 49 };
for (const ano of ['2026', '2022']) for (const cargo of ['DF', 'DE']) {
  const b = D.anos[ano][cargo];
  const unid = {};
  const key = p => (b.partidos[p] && b.partidos[p].fed) || p;
  let validos = 0;
  b.candidatos.forEach((c, i) => {
    if (c[5]) return;
    const v = b.votos[i].filter((_, k) => k % 2).reduce((a, x) => a + x, 0);
    const u = unid[key(c[2])] ??= { id: key(c[2]), votos: 0, cands: [] };
    u.votos += v; u.cands.push({ id: i, votos: v }); validos += v;
  });
  for (const [p, info] of Object.entries(b.partidos)) {
    if (info.anulado) continue;
    const v = info.leg.filter((_, k) => k % 2).reduce((a, x) => a + x, 0);
    const u = unid[key(p)] ??= { id: key(p), votos: 0, cands: [] };
    u.votos += v; validos += v;
  }
  const r = distribuirCadeiras(Object.values(unid), validos, VAGAS[cargo]);
  console.log(`\n${ano} ${cargo} válidos=${validos} QE=${r.qe}`);
  for (const u of r.unidades.filter(u => u.cadeiras || u.pctQE > 0.5).sort((a, b) => b.votos - a.votos))
    console.log(`  ${u.id.padEnd(22)} ${String(u.votos).padStart(8)} ${(u.pctQE * 100).toFixed(0).padStart(4)}%QE  QP=${u.porQP} média=${u.porMedia} total=${u.cadeiras}`);
  if (b.candidatos.some(c => c[4] === 's')) {
    const ofic = new Set(b.candidatos.map((c, i) => c[4] === 's' ? i : -1).filter(i => i >= 0));
    const calc = new Set(r.eleitos.map(e => e.id));
    const so = [...ofic].filter(i => !calc.has(i)).map(i => b.candidatos[i][1]);
    const sc = [...calc].filter(i => !ofic.has(i)).map(i => b.candidatos[i][1]);
    const viaQP = r.eleitos.filter(e => e.via === 'QP').length;
    const oficQP = b.candidatos.filter(c => /QP/i.test(c[3])).length;
    console.log(`  oficiais=${ofic.size} calculados=${calc.size} só oficial=${JSON.stringify(so)} só calculado=${JSON.stringify(sc)} QP calc=${viaQP} ofic=${oficQP}`);
  }
}
