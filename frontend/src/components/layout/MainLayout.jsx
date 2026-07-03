import { useState } from 'react';
import { Outlet } from 'react-router-dom';
import Sidebar from './Sidebar';
import Navbar from './Navbar';

const MainLayout = () => {
    const [sidebarOpen, setSidebarOpen] = useState(true);

    return (
        <div className="flex h-screen bg-background">
            {/* Sidebar */}
            {sidebarOpen && <Sidebar />}

            {/* Main Content */}
            <div className="flex-1 flex flex-col overflow-hidden">
                {/* Top Navbar */}
                <Navbar toggleSidebar={() => setSidebarOpen(!sidebarOpen)} />

                {/* Page Content */}
                <main className="flex-1 overflow-y-auto p-4 pt-3">
                    <Outlet />
                </main>
            </div>
        </div>
    );
};

export default MainLayout;
