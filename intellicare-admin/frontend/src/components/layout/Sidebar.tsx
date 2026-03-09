import { useState } from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  Droplets,
  Activity,
  HeartPulse,
  Ribbon,
  Settings,
  LogOut,
  ChevronLeft,
  ChevronRight,
  Shield,
  Building2,
  Globe,
} from 'lucide-react';
import { cn } from '@utils/formatters';
import { logout } from '@services/keycloak';
import { useAuthStore } from '@store/authStore';

const NAV_ITEMS = [
  { path: '/', icon: LayoutDashboard, label: 'Visão Geral' },
  { path: '/doenca/drc', icon: Droplets, label: 'Doença Renal Crônica', color: '#8b5cf6' },
  { path: '/doenca/diabetes', icon: Activity, label: 'Diabetes Mellitus', color: '#f59e0b' },
  { path: '/doenca/hipertensao', icon: HeartPulse, label: 'Hipertensão Arterial', color: '#ef4444' },
  { path: '/doenca/cancer', icon: Ribbon, label: 'Neoplasias', color: '#ec4899' },
];

const ADMIN_ITEMS = [
  { path: '/tenants', icon: Building2, label: 'Tenants / Secretarias' },
  { path: '/consolidado', icon: Globe, label: 'Consolidado Nacional' },
  { path: '/configuracoes', icon: Settings, label: 'Configurações' },
];

export default function Sidebar() {
  const [collapsed, setCollapsed] = useState(false);
  const user = useAuthStore((s) => s.user);

  return (
    <aside
      className={cn(
        'fixed left-0 top-0 h-screen flex flex-col bg-sidebar text-white z-50 transition-all duration-300',
        collapsed ? 'w-[68px]' : 'w-[260px]',
      )}
    >
      {/* Logo */}
      <div className="flex items-center gap-3 px-4 py-5 border-b border-white/10">
        <div className="w-9 h-9 rounded-lg bg-primary-600 flex items-center justify-center flex-shrink-0">
          <Shield className="h-5 w-5 text-white" />
        </div>
        {!collapsed && (
          <div className="overflow-hidden">
            <h1 className="text-sm font-bold tracking-wide">IntelliCare</h1>
            <p className="text-[10px] text-amber-300 uppercase tracking-widest">Admin</p>
          </div>
        )}
      </div>

      {/* Navigation */}
      <nav className="flex-1 py-4 px-2 space-y-1 overflow-y-auto">
        <p
          className={cn(
            'px-3 py-2 text-[10px] font-semibold uppercase tracking-widest text-slate-500',
            collapsed && 'text-center',
          )}
        >
          {collapsed ? '•••' : 'Programas de Saúde'}
        </p>
        {NAV_ITEMS.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            end={item.path === '/'}
            className={({ isActive }) =>
              cn(
                'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors group',
                isActive
                  ? 'bg-sidebar-active text-white'
                  : 'text-slate-300 hover:bg-sidebar-hover hover:text-white',
              )
            }
          >
            <item.icon
              className="h-5 w-5 flex-shrink-0"
              style={{ color: item.color }}
            />
            {!collapsed && <span className="truncate">{item.label}</span>}
          </NavLink>
        ))}
        <div className="my-3 border-t border-white/10" />
        <p className={cn('px-3 py-2 text-[10px] font-semibold uppercase tracking-widest text-slate-500', collapsed && 'text-center')}>
          {collapsed ? '•••' : 'Administração'}
        </p>
        {ADMIN_ITEMS.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            className={({ isActive }) =>
              cn(
                'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors',
                isActive
                  ? 'bg-sidebar-active text-white'
                  : 'text-slate-300 hover:bg-sidebar-hover hover:text-white',
              )
            }
          >
            <item.icon className="h-5 w-5 flex-shrink-0" />
            {!collapsed && <span className="truncate">{item.label}</span>}
          </NavLink>
        ))}
      </nav>

      {/* Bottom */}
      <div className="px-2 py-3 border-t border-white/10 space-y-1">
        <button
          onClick={logout}
          className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium text-slate-400 hover:bg-red-500/10 hover:text-red-400 transition-colors w-full"
        >
          <LogOut className="h-5 w-5 flex-shrink-0" />
          {!collapsed && <span>Sair</span>}
        </button>

        {/* User info */}
        {user && !collapsed && (
          <div className="px-3 py-2 mt-2">
            <p className="text-xs font-medium text-slate-300 truncate">{user.name}</p>
            <p className="text-[10px] text-amber-400/70 truncate">PLATFORM_ADMIN</p>
          </div>
        )}
      </div>

      {/* Collapse toggle */}
      <button
        onClick={() => setCollapsed(!collapsed)}
        className="absolute -right-3 top-20 w-6 h-6 rounded-full bg-slate-700 border-2 border-slate-600 flex items-center justify-center text-slate-400 hover:text-white hover:bg-slate-600 transition-colors"
      >
        {collapsed ? <ChevronRight className="h-3 w-3" /> : <ChevronLeft className="h-3 w-3" />}
      </button>
    </aside>
  );
}
