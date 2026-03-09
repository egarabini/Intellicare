import { Link } from 'react-router-dom';
import { Home } from 'lucide-react';

export default function NotFound() {
  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] text-slate-400">
      <p className="text-6xl font-bold mb-2">404</p>
      <p className="text-lg mb-6">Página não encontrada</p>
      <Link
        to="/"
        className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors text-sm font-medium"
      >
        <Home className="h-4 w-4" />
        Voltar ao Dashboard
      </Link>
    </div>
  );
}
