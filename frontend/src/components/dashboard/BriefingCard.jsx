import { AlertTriangle, Bot, RefreshCw, Zap } from 'lucide-react';

function ListaBriefing({ titulo, itens, icone, tipo }) {
  return (
    <div className={`briefing-lista ${tipo}`}>
      <h5>{icone} {titulo}</h5>
      {itens?.map((item) => <div key={item}>• {item}</div>)}
    </div>
  );
}

export default function BriefingCard({ briefing, carregando, onRecalcular }) {
  const temListas = briefing && (briefing.pontos_atencao?.length > 0 || briefing.oportunidades?.length > 0);
  return (
    <div className="briefing">
      <div className="briefing-topo">
        <div className="briefing-titulo">
          <Bot size={22} color="#818cf8" />
          <h3>{briefing ? briefing.titulo : 'Briefing Estratégico'}</h3>
          <span className="badge briefing-selo">Análise em Tempo Real</span>
        </div>
        <button type="button" className="briefing-botao" onClick={onRecalcular} disabled={carregando}>
          <RefreshCw size={12} className={carregando ? 'animate-spin' : ''} />
          {carregando ? 'Gerando Análise com Gemini...' : 'Recalcular Briefing'}
        </button>
      </div>

      <p className="briefing-resumo">
        {briefing ? briefing.resumo_executivo : 'Carregando análise estratégica do mix de produtos e tendências da sua loja...'}
      </p>

      {temListas && (
        <div className="briefing-listas">
          <ListaBriefing titulo="Pontos de Atenção no Estoque" itens={briefing.pontos_atencao}
            icone={<AlertTriangle size={14} />} tipo="atencao" />
          <ListaBriefing titulo="Oportunidades de Compra" itens={briefing.oportunidades}
            icone={<Zap size={14} />} tipo="oportunidade" />
        </div>
      )}
    </div>
  );
}
