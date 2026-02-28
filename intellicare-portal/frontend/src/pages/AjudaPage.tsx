import { useState } from 'react';
import { motion } from 'framer-motion';
import { HelpCircle, Search, Book, MessageCircle, Video, FileText, ChevronRight, ExternalLink } from 'lucide-react';

export default function AjudaPage() {
  const [searchTerm, setSearchTerm] = useState('');

  const helpCategories = [
    {
      icon: Book,
      title: 'Documentação',
      description: 'Guias completos e manuais de uso',
      articles: [
        'Primeiros passos com a IntelliCare',
        'Como configurar seu perfil',
        'Integração com sistemas de saúde',
        'Guia de boas práticas',
      ],
    },
    {
      icon: Video,
      title: 'Tutoriais em Vídeo',
      description: 'Aprenda visualmente com nossos tutoriais',
      articles: [
        'Introdução à plataforma',
        'Usando os Agentes de IA',
        'Interpretando dashboards',
        'Configurações avançadas',
      ],
    },
    {
      icon: MessageCircle,
      title: 'Suporte Técnico',
      description: 'Obtenha ajuda personalizada',
      articles: [
        'Abrir um chamado',
        'Chat ao vivo',
        'Agendar treinamento',
        'Reportar problema',
      ],
    },
    {
      icon: FileText,
      title: 'Base de Conhecimento',
      description: 'Artigos e soluções detalhadas',
      articles: [
        'Perguntas frequentes',
        'Solução de problemas',
        'Atualizações e novidades',
        'Notas de versão',
      ],
    },
  ];

  const quickLinks = [
    { title: 'Como começar', href: '#primeiros-passos' },
    { title: 'Configurar agentes', href: '#configurar-agentes' },
    { title: 'Importar dados', href: '#importar-dados' },
    { title: 'Gerar relatórios', href: '#relatorios' },
    { title: 'Convidar equipe', href: '#convidar-equipe' },
    { title: 'API e integrações', href: '#api' },
  ];

  const filteredCategories = helpCategories.filter((category) =>
    category.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
    category.articles.some((article) =>
      article.toLowerCase().includes(searchTerm.toLowerCase())
    )
  );

  return (
    <div className="min-h-screen bg-gradient-to-b from-neutral-50 to-white py-16">
      <div className="container">
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="text-center mb-12"
        >
          <div className="inline-flex items-center justify-center w-16 h-16 bg-primary-100 rounded-full mb-4">
            <HelpCircle className="w-8 h-8 text-primary-600" />
          </div>
          <h1 className="text-4xl font-bold text-neutral-900 mb-4">
            Central de Ajuda
          </h1>
          <p className="text-lg text-neutral-600 max-w-2xl mx-auto">
            Encontre respostas, guias e suporte para aproveitar ao máximo a IntelliCare
          </p>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.2 }}
          className="max-w-2xl mx-auto mb-12"
        >
          <div className="relative">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-neutral-400" />
            <input
              type="text"
              placeholder="Buscar ajuda..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-12 pr-4 py-4 rounded-xl border border-neutral-200 focus:border-primary-500 focus:ring-2 focus:ring-primary-200 outline-none transition-all text-lg"
            />
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.3 }}
          className="mb-12"
        >
          <h2 className="text-lg font-semibold text-neutral-900 mb-4 text-center">
            Links Rápidos
          </h2>
          <div className="flex flex-wrap justify-center gap-3">
            {quickLinks.map((link) => (
              <a
                key={link.title}
                href={link.href}
                className="inline-flex items-center gap-2 px-4 py-2 bg-white border border-neutral-200 rounded-full text-sm text-neutral-700 hover:border-primary-300 hover:text-primary-600 transition-colors"
              >
                {link.title}
                <ExternalLink className="w-3 h-3" />
              </a>
            ))}
          </div>
        </motion.div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {filteredCategories.map((category, index) => (
            <motion.div
              key={category.title}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.4 + index * 0.1 }}
              className="bg-white rounded-xl shadow-sm border border-neutral-200 p-6 hover:shadow-md transition-shadow"
            >
              <div className="flex items-start gap-4 mb-4">
                <div className="flex-shrink-0 w-12 h-12 bg-primary-100 rounded-lg flex items-center justify-center">
                  <category.icon className="w-6 h-6 text-primary-600" />
                </div>
                <div>
                  <h3 className="text-xl font-bold text-neutral-900">
                    {category.title}
                  </h3>
                  <p className="text-neutral-600 text-sm">
                    {category.description}
                  </p>
                </div>
              </div>
              <ul className="space-y-2">
                {category.articles.map((article) => (
                  <li key={article}>
                    <a
                      href="#"
                      className="flex items-center justify-between p-2 rounded-lg hover:bg-neutral-50 transition-colors group"
                    >
                      <span className="text-neutral-700 group-hover:text-primary-600">
                        {article}
                      </span>
                      <ChevronRight className="w-4 h-4 text-neutral-400 group-hover:text-primary-500" />
                    </a>
                  </li>
                ))}
              </ul>
            </motion.div>
          ))}
        </div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.8 }}
          className="mt-12 bg-gradient-to-r from-primary-600 to-secondary-600 rounded-2xl p-8 text-white text-center"
        >
          <h2 className="text-2xl font-bold mb-2">Não encontrou o que procurava?</h2>
          <p className="text-primary-100 mb-6">
            Nossa equipe de suporte está pronta para ajudar
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <a
              href="/contato"
              className="inline-flex items-center justify-center gap-2 px-6 py-3 bg-white text-primary-600 font-semibold rounded-lg hover:bg-primary-50 transition-colors"
            >
              <MessageCircle className="w-5 h-5" />
              Falar com Suporte
            </a>
            <a
              href="mailto:suporte@intellicare.com.br"
              className="inline-flex items-center justify-center gap-2 px-6 py-3 bg-primary-700 text-white font-semibold rounded-lg hover:bg-primary-800 transition-colors"
            >
              <FileText className="w-5 h-5" />
              Abrir Chamado
            </a>
          </div>
        </motion.div>
      </div>
    </div>
  );
}
