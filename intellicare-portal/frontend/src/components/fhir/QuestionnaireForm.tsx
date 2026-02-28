/**
 * QuestionnaireForm — renderiza e coleta respostas de um FHIR Questionnaire.
 * Suporta tipos: group, boolean, string, text, integer, decimal, date, choice.
 */

import { useState } from 'react';
import { ClipboardList, Send, ChevronDown } from 'lucide-react';
import {
  FHIRQuestionnaire,
  QuestionnaireItem,
  QuestionnaireResponseItem,
  codingDisplay,
} from './types';

// ── Types ──────────────────────────────────────────────────────────────────────

type Answers = Record<string, string | boolean | number | null>;

interface QuestionnaireFormProps {
  questionnaire: FHIRQuestionnaire;
  onSubmit: (response: { linkId: string; items: QuestionnaireResponseItem[] }) => void;
  className?: string;
}

// ── Main component ─────────────────────────────────────────────────────────────

export function QuestionnaireForm({ questionnaire, onSubmit, className }: QuestionnaireFormProps) {
  const [answers, setAnswers] = useState<Answers>({});
  const [submitted, setSubmitted] = useState(false);

  const setAnswer = (linkId: string, value: string | boolean | number | null) => {
    setAnswers(prev => ({ ...prev, [linkId]: value }));
  };

  const buildResponseItems = (items: QuestionnaireItem[]): QuestionnaireResponseItem[] => {
    // @ts-ignore - FHIR type compatibility with flatMap
    return items.flatMap(item => {
      if (item.type === 'group') {
        return [{
          linkId: item.linkId,
          item: buildResponseItems(item.item ?? []),
        }];
      }
      const val = answers[item.linkId];
      if (val === undefined || val === null || val === '') return [];
      const answer: QuestionnaireResponseItem['answer'] = [];
      if (item.type === 'boolean') answer.push({ valueBoolean: Boolean(val) });
      else if (item.type === 'integer') answer.push({ valueInteger: Number(val) });
      else if (item.type === 'decimal') answer.push({ valueDecimal: Number(val) });
      else if (item.type === 'date') answer.push({ valueDate: String(val) });
      else if (item.type === 'choice') answer.push({ valueCoding: { code: String(val) } });
      else answer.push({ valueString: String(val) });
      return [{ linkId: item.linkId, answer }];
    });
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const items = buildResponseItems(questionnaire.item ?? []);
    setSubmitted(true);
    onSubmit({ linkId: questionnaire.id ?? 'q', items });
  };

  if (submitted) {
    return (
      <div className={`bg-slate-800/50 border border-emerald-500/30 rounded-2xl p-8 text-center ${className ?? ''}`}>
        <div className="w-12 h-12 rounded-full bg-emerald-500/15 border border-emerald-500/30 flex items-center justify-center mx-auto mb-3">
          <Send className="w-5 h-5 text-emerald-400" />
        </div>
        <p className="text-white font-semibold">Respostas enviadas!</p>
        <p className="text-sm text-slate-500 mt-1">O questionário foi submetido com sucesso.</p>
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit} className={`space-y-4 ${className ?? ''}`}>
      <div className="bg-slate-800/50 border border-slate-700 rounded-2xl overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-700/50">
          <h3 className="text-sm font-semibold text-white flex items-center gap-2">
            <ClipboardList className="w-4 h-4 text-slate-400" />
            {questionnaire.title ?? 'Questionário'}
          </h3>
        </div>
        <div className="p-6 space-y-5">
          {questionnaire.item?.map(item => (
            <QuestionItem key={item.linkId} item={item} answers={answers} setAnswer={setAnswer} />
          ))}
        </div>
      </div>
      <button
        type="submit"
        className="w-full py-3 bg-blue-600 hover:bg-blue-500 text-white text-sm font-medium rounded-xl transition-colors flex items-center justify-center gap-2"
      >
        <Send className="w-4 h-4" />
        Enviar respostas
      </button>
    </form>
  );
}

// ── Question renderer ──────────────────────────────────────────────────────────

function QuestionItem({
  item,
  answers,
  setAnswer,
  indent = 0,
}: {
  item: QuestionnaireItem;
  answers: Answers;
  setAnswer: (linkId: string, value: string | boolean | number | null) => void;
  indent?: number;
}) {
  const value = answers[item.linkId] ?? '';
  const paddingClass = indent > 0 ? `pl-${Math.min(indent * 4, 12)}` : '';

  if (item.type === 'group') {
    return (
      <fieldset className={`space-y-4 ${paddingClass}`}>
        <legend className="text-xs font-semibold text-slate-400 uppercase tracking-wide">
          {item.text}
        </legend>
        {item.item?.map(child => (
          <QuestionItem key={child.linkId} item={child} answers={answers} setAnswer={setAnswer} indent={indent + 1} />
        ))}
      </fieldset>
    );
  }

  if (item.type === 'display') {
    return (
      <p className={`text-sm text-slate-400 ${paddingClass}`}>{item.text}</p>
    );
  }

  return (
    <div className={`space-y-1.5 ${paddingClass}`}>
      <label className="text-sm font-medium text-white flex items-center gap-1">
        {item.text}
        {item.required && <span className="text-red-400">*</span>}
      </label>

      {item.type === 'boolean' && (
        <div className="flex items-center gap-2">
          <input
            type="checkbox"
            id={item.linkId}
            checked={Boolean(value)}
            onChange={e => setAnswer(item.linkId, e.target.checked)}
            className="w-4 h-4 rounded border-slate-600 bg-slate-800 text-blue-500 focus:ring-blue-500"
          />
          <label htmlFor={item.linkId} className="text-sm text-slate-400">Sim</label>
        </div>
      )}

      {item.type === 'choice' && item.answerOption && (
        <div className="relative">
          <select
            value={String(value)}
            onChange={e => setAnswer(item.linkId, e.target.value)}
            required={item.required}
            className="w-full appearance-none bg-slate-900 border border-slate-700 rounded-xl px-4 py-2.5 text-sm text-white outline-none focus:border-blue-500/50 pr-10"
          >
            <option value="">Selecione...</option>
            {item.answerOption.map((opt, i) => (
              <option key={i} value={opt.valueCoding?.code ?? opt.valueString ?? String(opt.valueInteger ?? i)}>
                {opt.valueCoding ? codingDisplay({ coding: [opt.valueCoding] }) : opt.valueString ?? String(opt.valueInteger)}
              </option>
            ))}
          </select>
          <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500 pointer-events-none" />
        </div>
      )}

      {(item.type === 'string' || item.type === 'url') && (
        <input
          type="text"
          value={String(value)}
          onChange={e => setAnswer(item.linkId, e.target.value)}
          required={item.required}
          className="w-full bg-slate-900 border border-slate-700 rounded-xl px-4 py-2.5 text-sm text-white placeholder-slate-600 outline-none focus:border-blue-500/50 transition-colors"
        />
      )}

      {item.type === 'text' && (
        <textarea
          value={String(value)}
          onChange={e => setAnswer(item.linkId, e.target.value)}
          required={item.required}
          rows={3}
          className="w-full bg-slate-900 border border-slate-700 rounded-xl px-4 py-2.5 text-sm text-white placeholder-slate-600 outline-none focus:border-blue-500/50 transition-colors resize-none"
        />
      )}

      {(item.type === 'integer' || item.type === 'decimal') && (
        <input
          type="number"
          value={value === null ? '' : String(value)}
          onChange={e => setAnswer(item.linkId, e.target.value === '' ? null : Number(e.target.value))}
          required={item.required}
          step={item.type === 'decimal' ? 'any' : '1'}
          className="w-full bg-slate-900 border border-slate-700 rounded-xl px-4 py-2.5 text-sm text-white placeholder-slate-600 outline-none focus:border-blue-500/50 transition-colors"
        />
      )}

      {(item.type === 'date' || item.type === 'dateTime') && (
        <input
          type={item.type === 'date' ? 'date' : 'datetime-local'}
          value={String(value)}
          onChange={e => setAnswer(item.linkId, e.target.value)}
          required={item.required}
          className="w-full bg-slate-900 border border-slate-700 rounded-xl px-4 py-2.5 text-sm text-white outline-none focus:border-blue-500/50 transition-colors"
        />
      )}
    </div>
  );
}

export default QuestionnaireForm;
