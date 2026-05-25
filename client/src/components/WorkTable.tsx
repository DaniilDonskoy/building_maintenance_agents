import React, { useEffect, useState } from 'react';
import { TableData, Task } from '../types';
import axios from 'axios';

const WorkTable: React.FC = () => {
    const [data, setData] = useState<TableData>({ tasks: [] });
    const [loading, setLoading] = useState(true);

    /*useEffect(() => {
        fetch('/tables.json')
            .then(res => res.json())
            .then(setData)
            .catch(err => console.error('Ошибка:', err))
            .finally(() => setLoading(false));
    }, []);*/

    useEffect(() => {
        axios.get('/tables.json' )
            .then(res => setData(res.data))     // ← главное отличие
            .catch(err => console.error('Ошибка:', err))
            .finally(() => setLoading(false));
    }, []);


    if (loading) {
        return (
            <div style={{
                minHeight: '100vh',
                backgroundColor: '#0F172A',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: '#94A3B8',
                fontSize: '18px'
            }}>
                Загрузка...
            </div>
        );
    }

    return (
        <div style={tableStyles.pageWrapper}>
            <div style={tableStyles.container}>
                <h1 style={tableStyles.header}>📋 График плановых работ</h1>

                <div style={tableStyles.tableWrapper}>
                    <table style={tableStyles.table}>
                        <thead>
                        <tr style={tableStyles.theadRow}>
                            <th style={tableStyles.th}>Агент</th>
                            <th style={tableStyles.th}>Время</th>
                            <th style={tableStyles.th}>Здание</th>
                            <th style={{...tableStyles.th, textAlign: 'center'}}>Узел</th>
                            <th style={{...tableStyles.th, textAlign: 'right'}}>Стоимость</th>
                        </tr>
                        </thead>
                        <tbody>
                        {data.tasks.map((row: Task, idx: number) => (
                            <tr key={idx} style={tableStyles.tr}>
                                <td style={tableStyles.td}>{row.agent}</td>
                                <td style={{...tableStyles.td, color: '#94A3B8', fontFamily: 'monospace'}}>
                                    {row.time}
                                </td>
                                <td style={tableStyles.td}>{row.task}</td>
                                <td style={{...tableStyles.td, textAlign: 'center'}}>
                                    <span style={tableStyles.badge}>{row.node}</span>
                                </td>
                                <td style={{...tableStyles.td, textAlign: 'right', fontWeight: 'bold', color: '#38BDF8'}}>
                                    {row.cost.toLocaleString('ru-RU')} РУБ
                                </td>
                            </tr>
                        ))}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
};

const tableStyles: { [key: string]: React.CSSProperties } = {
    pageWrapper: {
        minHeight: '100vh',
        backgroundColor: '#0F172A',
        padding: '40px 20px',
        boxSizing: 'border-box',
    },
    container: {
        maxWidth: '1200px',           // чуть увеличил для лучшей читаемости
        margin: '0 auto',
        fontFamily: 'sans-serif',
        color: '#F8FAFC'
    },
    header: {
        textAlign: 'center',
        color: '#F8FAFC',
        fontWeight: 300,
        marginBottom: '40px',
        fontSize: '32px'
    },
    tableWrapper: {
        backgroundColor: '#1E293B',
        borderRadius: '20px',
        boxShadow: '0 10px 30px rgba(0,0,0,0.5)',
        overflow: 'hidden',
        border: '1px solid #334155'
    },
    table: {
        width: '100%',
        borderCollapse: 'collapse',
    },
    theadRow: {
        backgroundColor: '#334155',
        borderBottom: '2px solid #475569'
    },
    th: {
        padding: '18px 20px',
        fontSize: '14px',
        color: '#E2E8F0',           // сделал ярче
        textTransform: 'uppercase',
        letterSpacing: '0.5px',
        fontWeight: 600,            // ← более жирный шрифт
        textAlign: 'left',
        verticalAlign: 'middle'
    },
    tr: {
        borderBottom: '1px solid #334155'
    },
    td: {
        padding: '18px 20px',
        color: '#E2E8F0',
        fontSize: '14.5px',
        verticalAlign: 'middle'
    },
    badge: {
        backgroundColor: '#1E40AF',
        color: '#93C5FD',
        padding: '6px 16px',
        borderRadius: '9999px',
        fontSize: '13px',
        fontWeight: 600,
        display: 'inline-block',
        minWidth: '70px',
        textAlign: 'center'
    }
};

export default WorkTable;