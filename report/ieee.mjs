// Bibliographie au style IEEE, commune au rapport HTML/PDF et à la version LaTeX
// Une entrée structurée (bibliographie.json) -> texte IEEE. `it` met en italique, `q` met entre guillemets
// anglais avec la virgule à l'intérieur (convention IEEE) ; les deux dépendent de la sortie (Markdown ou LaTeX).
export function ieee(e, { it = (s) => `*${s}*`, q = (s) => `“${s},”` } = {}) {
  const a = e.author || []
  const auteurs = a.includes('et al.') ? `${a[0]} et al.`
    : a.length <= 1 ? (a[0] || '') : a.length === 2 ? `${a[0]} and ${a[1]}` : `${a.slice(0, -1).join(', ')}, and ${a.at(-1)}`
  const vnp = [e.volume && `vol. ${e.volume}`, e.number && `no. ${e.number}`, e.pages && `pp. ${e.pages}`].filter(Boolean)
  switch (e.type) {
    case 'article':
      return `${auteurs}, ${q(e.title)} ${it(e.journal)}, ${[...vnp, e.year].join(', ')}.`
    case 'inproceedings': {
      const serie = e.series ? `, ser. ${e.series}, vol. ${e.volume}. ${e.publisher}` : (e.volume ? `, vol. ${e.volume}` : '')
      return `${auteurs}, ${q(e.title)} in ${it(e.booktitle)}${serie}, ${e.year}.`
    }
    case 'book':
      return `${auteurs}, ${it(e.title)}. ${e.address}: ${e.publisher}, ${e.year}.`
    case 'incollection':
      return `${auteurs}, ${q(e.title)} in ${it(e.booktitle)}. ${e.address}: ${e.publisher}, ${e.year}.`
    case 'techreport':
      return `${auteurs}, ${q(e.title)} ${e.institution}, ${e.address}, ${e.number}, ${e.year}.`
    case 'standard':
      return `${auteurs}, ${it(e.title)}, ${e.number}, ${e.year}.`
    default:
      return `${auteurs}, ${q(e.title)} ${e.howpublished}, ${e.year}.`
  }
}

