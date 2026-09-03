(() => {
  const normalizar = value => String(value ?? '')
    .trim()
    .toUpperCase()
    .replace(/[^0-9A-Z]/g, '');

  const estruturaValida = value => /^[0-9A-Z]{12}[0-9]{2}$/.test(normalizar(value));

  const valorCaractere = char => char.charCodeAt(0) - 48;

  function calcularDigito(base, pesos) {
    const soma = base.split('').reduce((total, char, index) => total + valorCaractere(char) * pesos[index], 0);
    const resto = soma % 11;
    return resto < 2 ? 0 : 11 - resto;
  }

  function calcularDV(value) {
    const cnpj = normalizar(value);
    if (!/^[0-9A-Z]{12}$/.test(cnpj)) return '';
    const dv1 = calcularDigito(cnpj, [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]);
    const dv2 = calcularDigito(cnpj + dv1, [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]);
    return `${dv1}${dv2}`;
  }

  function validar(value) {
    const cnpj = normalizar(value);
    if (!estruturaValida(cnpj)) return false;
    return calcularDV(cnpj.slice(0, 12)) === cnpj.slice(12);
  }

  function formatar(value) {
    const cnpj = normalizar(value);
    if (cnpj.length !== 14) return cnpj;
    return `${cnpj.slice(0, 2)}.${cnpj.slice(2, 5)}.${cnpj.slice(5, 8)}/${cnpj.slice(8, 12)}-${cnpj.slice(12)}`;
  }

  const iguais = (a, b) => {
    const esquerda = normalizar(a);
    const direita = normalizar(b);
    return Boolean(esquerda && direita && esquerda === direita);
  };

  window.__omnixmlCnpj = Object.freeze({
    normalizar,
    estruturaValida,
    calcularDV,
    validar,
    formatar,
    iguais,
    versao: 'rfb-alfanumerico-v1',
  });
})();
