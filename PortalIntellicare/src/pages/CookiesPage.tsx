import { useState } from 'react';
import { motion } from 'framer-motion';
import { Cookie, Settings, Info, Check } from 'lucide-react';

export default function CookiesPage() {
  const [preferences, setPreferences] = useState({
    essential: true,
    analytics: false,
    marketing: false,
    functional: false,
  });

  const cookieTypes = [
    {
      id: 'essential',
      name: 'Cookies Essenciais',
      required: true,
      description: 'Necessários para o funcionamento básico da plataforma. Não podem ser desativados.',
      examples: ['Sessão de usuário', 'Autenticação', 'Segurança'],
    },
    {
      id: 'functional',
      name: 'Cookies Funcionais',
      required: false,
      description: 'Permitem funcionalidades avançadas e personalização da experiência.',
      examples: ['Preferências de idioma', 'Configurações de acessibilidade', 'Lembretes de login'],
    },
    {
      id: 'analytics',
      name: 'Cookies Analíticos',
      required: false,
      description: 'Ajudam a entender como os usuários interagem com a plataforma para melhorias contínuas.',
      examples: ['Google Analytics', 'Métricas de uso', 'Páginas visitadas'],
    },
    {
      id: 'marketing',
      name: 'Cookies de Marketing',
      required: false,
      description: 'Utilizados para personalizar anúncios e medir eficácia de campanhas.',
      examples: ['Remarketing', 'Conversões', 'Redes sociais'],
    },
  ];

  const handleToggle = (id: string) => {
    if (id === 'essential') return;
    setPreferences((prev) => ({
      ...prev,
      [id]: !prev[id as keyof typeof prev],
    }));
  };

  const handleSave = () => {
    localStorage.setItem('cookiePreferences', JSON.stringify(preferences));
    alert('Preferências salvas com sucesso!');
  };

  const handleAcceptAll = () => {
    const allAccepted = {
      essential: true,
      analytics: true,
      marketing: true,
      functional: true,
    };
    setPreferences(allAccepted);
    localStorage.setItem('cookiePreferences', JSON.stringify(allAccepted));
    alert('Todas as categorias de cookies foram aceitas!');
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-neutral-50 to-white py-16">
      <div className="container max-w-4xl">
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="text-center mb-12"
        >
          <div className="inline-flex items-center justify-center w-16 h-16 bg-primary-100 rounded-full mb-4">
            <Cookie className="w-8 h-8 text-primary-600" />
          </div>
          <h1 className="text-4xl font-bold text-neutral-900 mb-4">
            Política de Cookies
          </h1>
          <p className="text-lg text-neutral-600">
            Última atualização: {new Date().toLocaleDateString('pt-BR')}
          </p>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.2 }}
          className="bg-white rounded-2xl shadow-sm border border-neutral-200 p-8 mb-8"
        >
          <div className="flex items-start gap-4">
            <div className="flex-shrink-0 w-12 h-12 bg-primary-100 rounded-lg flex items-center justify-center">
              <Info className="w-6 h-6 text-primary-600" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-neutral-900 mb-3">
                O que são Cookies?
              </h2>
              <p className="text-neutral-600 leading-relaxed">
                Cookies são pequenos arquivos de texto armazenados em seu dispositivo quando você 
                visita um site. Eles nos ajudam a fornecer uma melhor experiência, lembrando suas 
                preferências, entendendo como você usa nossa plataforma e personalizando o conteúdo.
              </p>
            </div>
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.3 }}
          className="bg-white rounded-2xl shadow-sm border border-neutral-200 p-8 mb-8"
        >
          <div className="flex items-start gap-4 mb-6">
            <div className="flex-shrink-0 w-12 h-12 bg-primary-100 rounded-lg flex items-center justify-center">
              <Settings className="w-6 h-6 text-primary-600" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-neutral-900 mb-2">
                Gerenciar Preferências
              </h2>
              <p className="text-neutral-600">
                Escolha quais categorias de cookies você deseja aceitar. Cookies essenciais 
                são obrigatórios para o funcionamento da plataforma.
              </p>
            </div>
          </div>

          <div className="space-y-4">
            {cookieTypes.map((cookie) => (
              <div
                key={cookie.id}
                className={`border rounded-xl p-4 transition-colors ${
                  preferences[cookie.id as keyof typeof preferences]
                    ? 'border-primary-200 bg-primary-50'
                    : 'border-neutral-200 bg-white'
                }`}
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-grow">
                    <div className="flex items-center gap-2 mb-2">
                      <h3 className="font-semibold text-neutral-900">
                        {cookie.name}
                      </h3>
                      {cookie.required && (
                        <span className="px-2 py-0.5 bg-neutral-200 text-neutral-700 text-xs rounded-full">
                          Obrigatório
                        </span>
                      )}
                    </div>
                    <p className="text-sm text-neutral-600 mb-2">
                      {cookie.description}
                    </p>
                    <div className="flex flex-wrap gap-2">
                      {cookie.examples.map((example) => (
                        <span
                          key={example}
                          className="px-2 py-1 bg-neutral-100 text-neutral-600 text-xs rounded"
                        >
                          {example}
                        </span>
                      ))}
                    </div>
                  </div>
                  <button
                    onClick={() => handleToggle(cookie.id)}
                    disabled={cookie.required}
                    className={`flex-shrink-0 w-12 h-6 rounded-full transition-colors relative ${
                      preferences[cookie.id as keyof typeof preferences]
                        ? 'bg-primary-600'
                        : 'bg-neutral-300'
                    } ${cookie.required ? 'cursor-not-allowed opacity-60' : 'cursor-pointer'}`}
                  >
                    <span
                      className={`absolute top-1 w-4 h-4 bg-white rounded-full transition-transform ${
                        preferences[cookie.id as keyof typeof preferences]
                          ? 'translate-x-7'
                          : 'translate-x-1'
                      }`}
                    />
                  </button>
                </div>
              </div>
            ))}
          </div>

          <div className="flex flex-col sm:flex-row gap-3 mt-6 pt-6 border-t border-neutral-200">
            <button
              onClick={handleSave}
              className="flex-1 inline-flex items-center justify-center gap-2 px-6 py-3 bg-primary-600 text-white font-semibold rounded-lg hover:bg-primary-700 transition-colors"
            >
              <Check className="w-5 h-5" />
              Salvar Preferências
            </button>
            <button
              onClick={handleAcceptAll}
              className="flex-1 inline-flex items-center justify-center gap-2 px-6 py-3 bg-neutral-100 text-neutral-700 font-semibold rounded-lg hover:bg-neutral-200 transition-colors"
            >
              Aceitar Todos
            </button>
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.5 }}
          className="bg-white rounded-xl shadow-sm border border-neutral-200 p-6"
        >
          <h2 className="text-xl font-bold text-neutral-900 mb-4">
            Como Gerenciar Cookies no Navegador
          </h2>
          <div className="space-y-3 text-neutral-600">
            <p>
              Além das configurações acima, você também pode gerenciar cookies diretamente 
              no seu navegador:
            </p>
            <ul className="space-y-2 ml-4">
              <li className="flex items-start gap-2">
                <span className="text-primary-500">•</span>
                <span>
                  <strong>Chrome:</strong> Configurações {'>'} Privacidade e segurança {'>'} Cookies
                </span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-primary-500">•</span>
                <span>
                  <strong>Firefox:</strong> Opções {'>'} Privacidade e Segurança {'>'} Cookies
                </span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-primary-500">•</span>
                <span>
                  <strong>Safari:</strong> Preferências {'>'} Privacidade {'>'} Cookies
                </span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-primary-500">•</span>
                <span>
                  <strong>Edge:</strong> Configurações {'>'} Cookies e permissões de site
                </span>
              </li>
            </ul>
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.6, delay: 0.6 }}
          className="mt-8 text-center text-sm text-neutral-500"
        >
          <p>
            Para mais informações sobre como usamos seus dados, consulte nossa{' '}
            <a href="/privacidade" className="text-primary-600 hover:underline">
              Política de Privacidade
            </a>
            .
          </p>
        </motion.div>
      </div>
    </div>
  );
}
