import React, { useState } from 'react';
import BuildingGraph from '../BuildingGraph';
import HousesMap from '../components/HousesMap';

const GraphPage = () => {
    // Состояние для хранения индекса выбранного дома
    const [selectedHouseIndex, setSelectedHouseIndex] = useState<number | null>(null);

    // Если индекс выбран — показываем граф
    if (selectedHouseIndex !== null) {
        return (
            <div style={{ position: 'relative', background: '#0F172A' }}>
                {/* Кнопка возврата */}
                <button
                    onClick={() => setSelectedHouseIndex(null)}
                    style={backButtonStyle}
                >
                    ← Вернуться к выбору дома
                </button>

                {/* Передаем индекс в BuildingGraph */}
                <BuildingGraph houseIndex={selectedHouseIndex} />
            </div>
        );
    }

    // Если ничего не выбрано — показываем список точек
    return <HousesMap onSelectHouse={(idx) => setSelectedHouseIndex(idx)} />;
};

const backButtonStyle: React.CSSProperties = {
    position: 'absolute',
    top: '20px',
    left: '20px',
    zIndex: 1001,
    padding: '12px 20px',
    backgroundColor: 'rgba(56, 189, 248, 0.15)',
    color: '#38BDF8',
    border: '1px solid #38BDF8',
    borderRadius: '12px',
    cursor: 'pointer',
    fontWeight: 'bold',
    backdropFilter: 'blur(5px)',
    transition: 'all 0.3s'
};

export default GraphPage;