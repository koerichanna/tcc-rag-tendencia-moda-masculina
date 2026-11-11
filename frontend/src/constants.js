// Mesmos valores do enum CategoriaProduto no backend (schemas.py).
export const CATEGORIAS = ['Camisas', 'Calças', 'Camisetas', 'Calçados', 'Bermudas', 'Jaquetas'];

export const PERGUNTAS_EXEMPLO = [
  { texto: 'Devo comprar mais calças jeans skinny para esta coleção?', cat: 'Calças' },
  { texto: 'Vale a pena investir em camisas de linho para o verão?', cat: 'Camisas' },
  { texto: 'O tênis de couro branco minimalista ainda tem giro seguro?', cat: 'Calçados' },
  { texto: 'Qual o risco de colocar bermudas de alfaiataria na vitrine?', cat: 'Bermudas' },
];

export const PRODUTO_VAZIO = {
  nome: '',
  categoria: 'Camisas',
  preco_medio: '',
  custo_aquisicao: '',
  quantidade_estoque: '',
  estoque_minimo: 5,
};
