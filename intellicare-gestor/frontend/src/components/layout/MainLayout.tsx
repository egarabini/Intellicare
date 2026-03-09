import { Outlet } from 'react-router-dom';
import Sidebar from './Sidebar';

export default function MainLayout() {
  return (
    <div className="min-h-screen bg-surface">
      <Sidebar />
      <main className="ml-[260px] p-6 transition-all duration-300">
        <Outlet />
      </main>
    </div>
  );
}
