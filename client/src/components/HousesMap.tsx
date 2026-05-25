import React, { useState, useEffect } from "react";

interface HouseData {
    x: number;
    y: number;
    nodes: any[];
    edges: any[];
}

interface HousesMapProps {
    onSelectHouse: (index: number) => void;
}

const HousesMap: React.FC<HousesMapProps> = ({ onSelectHouse }) => {
    const [houses, setHouses] = useState<HouseData[]>([]);
    const [hoveredIdx, setHoveredIdx] = useState<number | null>(null);

    useEffect(() => {
        // Загружаем данные из public/complex_graph_example.json
        fetch("/complex_graph_example.json")
            .then((res) => res.json())
            .then((data) => setHouses(data.houses || []))
            .catch(err => console.error("Ошибка загрузки домов:", err));
    }, []);

    // Функция для расчета статистики дома на лету
    const getStats = (house: HouseData) => {
        const floors = new Set(house.nodes.map(n => n.features?.floor).filter(f => f !== undefined));
        const sections = new Set(house.nodes.map(n => n.features?.section).filter(s => s !== undefined));
        return {
            floors: floors.size,
            sections: sections.size,
            nodesCount: house.nodes.length
        };
    };

    return (
        <div style={styles.wrapper}>
            <h2 style={styles.title}>Выберите объект для визуализации</h2>
            <div style={styles.container}>
                {houses.map((house, idx) => {
                    const stats = getStats(house);
                    const isHovered = hoveredIdx === idx;

                    return (
                        <div
                            key={idx}
                            style={{
                                ...styles.houseCard,
                                transform: isHovered ? "translateY(-10px) scale(1.05)" : "translateY(0) scale(1)",
                                borderColor: isHovered ? "#38BDF8" : "#334155"
                            }}
                            onMouseEnter={() => setHoveredIdx(idx)}
                            onMouseLeave={() => setHoveredIdx(null)}
                            onClick={() => onSelectHouse(idx)}
                        >
                            <div style={{
                                ...styles.point,
                                boxShadow: isHovered ? "0 0 20px #38BDF8" : "none"
                            }}>
                                <div style={styles.innerPoint} />
                            </div>

                            <h3 style={styles.houseName}>Дом №{idx + 1}</h3>

                            <div style={styles.statsGrid}>
                                <div style={styles.statItem}>
                                    <span style={styles.statLabel}>Координаты:</span>
                                    <span>{house.x}, {house.y}</span>
                                </div>
                                <div style={styles.statItem}>
                                    <span style={styles.statLabel}>Этажность:</span>
                                    <span>{stats.floors}</span>
                                </div>
                                <div style={styles.statItem}>
                                    <span style={styles.statLabel}>Секции:</span>
                                    <span>{stats.sections}</span>
                                </div>
                            </div>

                            {isHovered && (
                                <div style={styles.clickHint}>Нажмите, чтобы открыть граф</div>
                            )}
                        </div>
                    );
                })}
            </div>
        </div>
    );
};

const styles: { [key: string]: React.CSSProperties } = {
    wrapper: {
        background: "#0F172A",
        minHeight: "calc(100vh - 100px)",
        padding: "40px 20px",
        fontFamily: "'Inter', sans-serif",
        color: "#F8FAFC"
    },
    title: {
        textAlign: "center",
        fontWeight: 300,
        fontSize: "28px",
        marginBottom: "50px",
        letterSpacing: "1px"
    },
    container: {
        display: "flex",
        flexWrap: "wrap",
        justifyContent: "center",
        gap: "30px",
        maxWidth: "1200px",
        margin: "0 auto"
    },
    houseCard: {
        width: "260px",
        background: "#1E293B",
        border: "1px solid #334155",
        borderRadius: "16px",
        padding: "25px",
        cursor: "pointer",
        transition: "all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275)",
        position: "relative",
        display: "flex",
        flexDirection: "column",
        alignItems: "center"
    },
    point: {
        width: "50px",
        height: "50px",
        borderRadius: "50%",
        background: "rgba(56, 189, 248, 0.1)",
        border: "2px solid #38BDF8",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        marginBottom: "15px"
    },
    innerPoint: {
        width: "12px",
        height: "12px",
        borderRadius: "50%",
        background: "#38BDF8",
    },
    houseName: {
        margin: "0 0 15px 0",
        fontSize: "20px",
        color: "#38BDF8"
    },
    statsGrid: {
        width: "100%",
        fontSize: "13px",
        lineHeight: "1.6",
        color: "#94A3B8"
    },
    statItem: {
        display: "flex",
        justifyContent: "space-between",
        borderBottom: "1px solid #334155",
        padding: "4px 0"
    },
    statLabel: {
        fontWeight: "bold"
    },
    clickHint: {
        marginTop: "15px",
        fontSize: "12px",
        color: "#38BDF8",
        fontStyle: "italic",
        animation: "pulse 2s infinite"
    }
};

export default HousesMap;