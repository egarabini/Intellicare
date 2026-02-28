import { Link } from 'react-router-dom';
import { Mail, Phone, MapPin, Github, Linkedin, Twitter } from 'lucide-react';

const Footer = () => {
  const currentYear = new Date().getFullYear();

  const footerLinks = {
    produto: [
      { label: 'Agentes', path: '/agentes' },
      { label: 'Dashboards', path: '/dashboards' },
      { label: 'Casos de Uso', path: '/casos-de-uso' },
      { label: 'Documentação', path: '/documentacao' },
    ],
    empresa: [
      { label: 'Sobre Nós', path: '/sobre' },
      { label: 'Equipe', path: '/equipe' },
      { label: 'Carreiras', path: '/carreiras' },
      { label: 'Blog', path: '/blog' },
    ],
    suporte: [
      { label: 'Central de Ajuda', path: '/ajuda' },
      { label: 'Contato', path: '/contato' },
      { label: 'FAQ', path: '/faq' },
      { label: 'Status', path: '/status' },
    ],
    legal: [
      { label: 'Termos de Uso', path: '/termos' },
      { label: 'Política de Privacidade', path: '/privacidade' },
      { label: 'Cookies', path: '/cookies' },
      { label: 'LGPD', path: '/lgpd' },
    ],
  };

  const socialLinks = [
    { icon: Github, href: 'https://github.com/intellicare', label: 'GitHub' },
    { icon: Linkedin, href: 'https://linkedin.com/company/intellicare', label: 'LinkedIn' },
    { icon: Twitter, href: 'https://twitter.com/intellicare', label: 'Twitter' },
  ];

  return (
    <footer className="bg-neutral-900 text-neutral-300">
      <div className="container py-12">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-6 gap-8 mb-8">
          <div className="lg:col-span-2">
            <div className="flex items-center space-x-3 mb-4">
              <div className="w-12 h-12 bg-gradient-primary rounded-lg flex items-center justify-center">
                <span className="text-white font-bold text-xl">IC</span>
              </div>
              <div>
                <h3 className="text-xl font-bold text-white">IntelliCare</h3>
                <p className="text-xs text-neutral-400">
                  Agentes Inteligentes em Saúde
                </p>
              </div>
            </div>
            <p className="text-sm text-neutral-400 mb-4">
              Transformando a saúde pública brasileira através de agentes
              inteligentes baseados em IA, promovendo eficiência, qualidade e
              acesso universal aos serviços de saúde.
            </p>
            <div className="space-y-2">
              <div className="flex items-center space-x-2 text-sm">
                <Mail className="w-4 h-4 text-primary-400" />
                <a
                  href="mailto:contato@intellicare.com.br"
                  className="hover:text-primary-400 transition-colors"
                >
                  contato@intellicare.com.br
                </a>
              </div>
              <div className="flex items-center space-x-2 text-sm">
                <Phone className="w-4 h-4 text-primary-400" />
                <a
                  href="tel:+5511999999999"
                  className="hover:text-primary-400 transition-colors"
                >
                  (11) 99999-9999
                </a>
              </div>
              <div className="flex items-center space-x-2 text-sm">
                <MapPin className="w-4 h-4 text-primary-400" />
                <span>São Paulo, SP - Brasil</span>
              </div>
            </div>
          </div>

          <div>
            <h4 className="text-white font-semibold mb-4">Produto</h4>
            <ul className="space-y-2">
              {footerLinks.produto.map((link) => (
                <li key={link.path}>
                  <Link
                    to={link.path}
                    className="text-sm hover:text-primary-400 transition-colors"
                  >
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          <div>
            <h4 className="text-white font-semibold mb-4">Empresa</h4>
            <ul className="space-y-2">
              {footerLinks.empresa.map((link) => (
                <li key={link.path}>
                  <Link
                    to={link.path}
                    className="text-sm hover:text-primary-400 transition-colors"
                  >
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          <div>
            <h4 className="text-white font-semibold mb-4">Suporte</h4>
            <ul className="space-y-2">
              {footerLinks.suporte.map((link) => (
                <li key={link.path}>
                  <Link
                    to={link.path}
                    className="text-sm hover:text-primary-400 transition-colors"
                  >
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          <div>
            <h4 className="text-white font-semibold mb-4">Legal</h4>
            <ul className="space-y-2">
              {footerLinks.legal.map((link) => (
                <li key={link.path}>
                  <Link
                    to={link.path}
                    className="text-sm hover:text-primary-400 transition-colors"
                  >
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>
        </div>

        <div className="border-t border-neutral-800 pt-8">
          <div className="flex flex-col md:flex-row justify-between items-center space-y-4 md:space-y-0">
            <p className="text-sm text-neutral-400">
              © {currentYear} IntelliCare. Todos os direitos reservados.
            </p>
            <div className="flex items-center space-x-4">
              {socialLinks.map((social) => (
                <a
                  key={social.label}
                  href={social.href}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="w-10 h-10 rounded-full bg-neutral-800 flex items-center justify-center hover:bg-primary-600 transition-colors"
                  aria-label={social.label}
                >
                  <social.icon className="w-5 h-5" />
                </a>
              ))}
            </div>
          </div>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
