INSERT INTO public.prompt_templates (prompt_key, version, content, is_active, description)
VALUES (
  'oswaldo_interaction_check', 1,
  'Você é um farmacologista clínico. Analise a interação entre {drug_a} e {drug_b}.
Se houver interação clinicamente relevante, responda em JSON:
{"has_interaction": true, "severity": "GRAVE" ou "MODERADO" ou "LEVE", "effect": "...", "recommendation": "..."}.
Se não houver interação relevante: {"has_interaction": false}.
Seja conciso e baseado em evidências.',
  TRUE,
  'Verificação de interação medicamentosa via LLM'
) ON CONFLICT (prompt_key, version) DO NOTHING;
