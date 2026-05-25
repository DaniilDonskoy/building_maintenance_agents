import { NavLink } from 'react-router-dom';
import React from 'react';

const Navbar = () => {
    return (
        <nav style={navStyles.navbar}>
            <div style={navStyles.container}>
                <NavLink to="/" style={({ isActive }) => ({
                    ...navStyles.link,
                    ...(isActive ? navStyles.activeLink : {})
                })}>
                    📊 Граф дома
                </NavLink>

                <NavLink to="/constructor" style={({ isActive }) => ({
                    ...navStyles.link,
                    ...(isActive ? navStyles.activeLink : {})
                })}>
                    🏗️ Конструктор домов
                </NavLink>

                <NavLink to="/upload" style={({ isActive }) => ({
                    ...navStyles.link,
                    ...(isActive ? navStyles.activeLink : {})
                })}>
                    📤 Загрузка заявок
                </NavLink>

                <NavLink to="/table" style={({ isActive }) => ({
                    ...navStyles.link,
                    ...(isActive ? navStyles.activeLink : {})
                })}>
                    📋 График работ
                </NavLink>
            </div>
        </nav>
    );
};

const navStyles: { [key: string]: React.CSSProperties } = {
    navbar: {
        display: 'flex',
        justifyContent: 'center',
        padding: '25px 0',
        backgroundColor: '#0F172A', //backgroundColor: '#ffffff',
        position: 'sticky',
        top: 0,
        zIndex: 1000,
        boxShadow: '0 2px 10px rgba(0,0,0,0.03)'
    },
    container: {
        display: 'flex',
        gap: '15px',
        backgroundColor: '#1E293B',//backgroundColor: '#f1f3f4',
        padding: '6px',
        borderRadius: '18px',
    },
    link: {
        padding: '10px 24px',
        borderRadius: '14px',
        textDecoration: 'none',
        fontSize: '15px',
        fontWeight: 500,
        color: '#94A3B8',//color: '#5f6368',
        transition: 'all 0.3s ease',
    },
    activeLink: {
        backgroundColor: '#38BDF8',//backgroundColor: '#ffffff',
        color: '#0F172A', //color: '#1a73e8',
        boxShadow: '0 4px 12px rgba(0,0,0,0.08)',
    }
};

export default Navbar;