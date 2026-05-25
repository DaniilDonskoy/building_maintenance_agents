import React, { useState } from "react";
import axios from "axios";
import { useNavigate } from "react-router-dom";

interface HouseFormData {
    sections: number;
    floors: number;
    elevs_per_section: number;
    flats_per_section: number;
    street: string;
    number: string;
}

const ConstructorPage: React.FC = () => {
    const navigate = useNavigate();
    const [mode, setMode] = useState<"menu" | "single" | "multiple">("menu");

    const [singleData, setSingleData] = useState<HouseFormData>({
        sections: 1,
        floors: 9,
        elevs_per_section: 1,
        flats_per_section: 4,
        street: "",
        number: "",
    });

    const [multipleData, setMultipleData] = useState<HouseFormData[]>([
        {
            sections: 1,
            floors: 9,
            elevs_per_section: 1,
            flats_per_section: 4,
            street: "",
            number: "",
        }
    ]);

    const handleSingleSubmit = async () => {
        if (!singleData.street || !singleData.number) {
            alert("Пожалуйста, заполните улицу и номер дома");
            return;
        }
        try {
            await axios.post("/api/constructor/single", singleData);
            alert("Здание успешно отправлено на сервер!");
            navigate("/");
        } catch (err) {
            console.error(err);
            alert("Ошибка при отправке на сервер");
        }
    };

    const handleMultipleSubmit = async () => {
        const emptyHouse = multipleData.find(h => !h.street || !h.number);
        if (emptyHouse) {
            alert("Пожалуйста, заполните улицу и номер дома для всех зданий");
            return;
        }
        try {
            await axios.post("/api/constructor/multiple", { houses: multipleData });
            alert("Все здания успешно отправлены!");
            navigate("/");
        } catch (err) {
            console.error(err);
            alert("Ошибка при отправке");
        }
    };

    const updateSingle = (field: keyof HouseFormData, value: string | number) => {
        setSingleData(prev => ({ ...prev, [field]: value }));
    };

    const updateMultiple = (index: number, field: keyof HouseFormData, value: string | number) => {
        const newData = [...multipleData];
        newData[index] = { ...newData[index], [field]: value };
        setMultipleData(newData);
    };

    const addHouse = () => {
        setMultipleData(prev => [...prev, {
            sections: 1,
            floors: 9,
            elevs_per_section: 1,
            flats_per_section: 4,
            street: "",
            number: "",
        }]);
    };

    const removeHouse = (index: number) => {
        if (multipleData.length === 1) return;
        setMultipleData(prev => prev.filter((_, i) => i !== index));
    };

    const renderForm = (
        data: HouseFormData,
        onChange: (field: keyof HouseFormData, value: any) => void,
        showButtons = true,
        index?: number
    ) => (
        <div style={styles.formCard}>
            {index !== undefined && <div style={styles.houseNumber}>Дом №{index + 1}</div>}

            <div style={styles.formGroup}>
                <label>Количество секций</label>
                <input
                    type="number"
                    min="1"
                    value={data.sections}
                    onChange={(e) => onChange("sections", parseInt(e.target.value) || 1)}
                    onFocus={(e) => e.target.select()}
                    style={styles.input}
                />
            </div>

            <div style={styles.formGroup}>
                <label>Количество этажей</label>
                <input
                    type="number"
                    min="1"
                    value={data.floors}
                    onChange={(e) => onChange("floors", parseInt(e.target.value) || 1)}
                    onFocus={(e) => e.target.select()}
                    style={styles.input}
                />
            </div>

            <div style={styles.formGroup}>
                <label>Количество лифтов на секцию</label>
                <input
                    type="number"
                    min="0"
                    value={data.elevs_per_section}
                    onChange={(e) => onChange("elevs_per_section", parseInt(e.target.value) || 0)}
                    onFocus={(e) => e.target.select()}
                    style={styles.input}
                />
            </div>

            <div style={styles.formGroup}>
                <label>Количество квартир на секцию</label>
                <input
                    type="number"
                    min="1"
                    value={data.flats_per_section}
                    onChange={(e) => onChange("flats_per_section", parseInt(e.target.value) || 1)}
                    onFocus={(e) => e.target.select()}
                    style={styles.input}
                />
            </div>

            <div style={styles.formGroup}>
                <label>Улица</label>
                <input
                    type="text"
                    value={data.street}
                    onChange={(e) => onChange("street", e.target.value)}
                    style={styles.input}
                    placeholder="ул. Пушкина"
                />
            </div>

            <div style={styles.formGroup}>
                <label>Номер здания</label>
                <input
                    type="text"
                    value={data.number}
                    onChange={(e) => onChange("number", e.target.value)}
                    style={styles.input}
                    placeholder="12с1"
                />
            </div>

            {showButtons && (
                <button onClick={handleSingleSubmit} style={styles.submitButton}>
                    Создать здание
                </button>
            )}
        </div>
    );

    return (
        <div style={styles.wrapper}>
            {(mode === "single" || mode === "multiple") && (
                <div style={styles.header}>
                    <button onClick={() => setMode("menu")} style={styles.backButton}>
                        ← Назад
                    </button>
                    <h1 style={styles.title}>
                        {mode === "single" ? "Создание одного здания" : "Создание нескольких зданий"}
                    </h1>
                </div>
            )}

            {mode === "menu" && (
                <>
                    <h1 style={styles.mainTitle}>Конструктор домов</h1>
                    <div style={styles.menuContainer}>
                        <div style={styles.menuCard} onClick={() => setMode("single")}>
                            <div style={styles.icon}>🏢</div>
                            <h3>Сконструировать одно здание</h3>

                        </div>

                        <div style={styles.menuCard} onClick={() => setMode("multiple")}>
                            <div style={styles.icon}>🏘️</div>
                            <h3>Сконструировать несколько зданий</h3>

                        </div>
                    </div>
                </>
            )}

            {mode === "single" && (
                <div style={styles.formContainer}>
                    {renderForm(singleData, updateSingle)}
                    <button onClick={() => setMode("menu")} style={styles.backToMenu}>
                        ← Вернуться к выбору режима
                    </button>
                </div>
            )}

            {mode === "multiple" && (
                <div style={styles.formContainer}>
                    <div style={{ textAlign: "center", marginBottom: "25px" }}>
                        <button onClick={addHouse} style={styles.addButton}>+ Добавить здание</button>
                    </div>

                    {multipleData.map((house, idx) => (
                        <div key={idx} style={{ position: "relative", marginBottom: "40px" }}>
                            {renderForm(
                                house,
                                (field, value) => updateMultiple(idx, field, value),
                                false,
                                idx
                            )}
                            {multipleData.length > 1 && (
                                <button
                                    onClick={() => removeHouse(idx)}
                                    style={styles.removeButton}
                                >
                                    ✕
                                </button>
                            )}
                        </div>
                    ))}

                    <button onClick={handleMultipleSubmit} style={styles.submitButtonBig}>
                        Создать комплекс
                    </button>

                    <button onClick={() => setMode("menu")} style={styles.backToMenu}>
                        ← Вернуться к выбору режима
                    </button>
                </div>
            )}
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
    mainTitle: {
        textAlign: "center",
        fontSize: "32px",
        fontWeight: 300,
        marginBottom: "50px",
        letterSpacing: "1px"
    },
    header: {
        display: "flex",
        alignItems: "center",
        gap: "20px",
        marginBottom: "40px"
    },
    backButton: {
        background: "#334155",
        color: "#F8FAFC",
        border: "none",
        padding: "10px 18px",
        borderRadius: "12px",
        cursor: "pointer",
        fontSize: "16px",
        whiteSpace: "nowrap"
    },
    title: {
        fontSize: "28px",
        fontWeight: 400,
        margin: 0,
        letterSpacing: "1px"
    },
    menuContainer: {
        display: "flex",
        justifyContent: "center",
        gap: "40px",
        flexWrap: "wrap"
    },
    menuCard: {
        width: "340px",
        background: "#1E293B",
        border: "1px solid #334155",
        borderRadius: "20px",
        padding: "40px 30px",
        textAlign: "center",
        cursor: "pointer",
        transition: "all 0.3s ease",
    },
    icon: {
        fontSize: "72px",
        marginBottom: "20px"
    },
    formContainer: {
        maxWidth: "720px",
        margin: "0 auto"
    },
    formCard: {
        background: "#1E293B",
        border: "1px solid #334155",
        borderRadius: "16px",
        padding: "35px",
        position: "relative"
    },
    houseNumber: {
        position: "absolute",
        top: "-14px",
        left: "25px",
        background: "#1E293B",
        padding: "4px 16px",
        borderRadius: "999px",
        fontSize: "14px",
        color: "#38BDF8",
        border: "1px solid #334155",
        zIndex: 2
    },
    formGroup: {
        marginBottom: "22px"
    },
    input: {
        width: "100%",
        padding: "14px 16px",
        background: "#0F172A",
        border: "1px solid #475569",
        borderRadius: "10px",
        color: "#F8FAFC",
        fontSize: "16px",
        MozAppearance: "textfield",
        WebkitAppearance: "none",
    },
    // Дополнительные стили для скрытия стрелок number input
    inputNumber: {
        WebkitAppearance: "none",
        MozAppearance: "textfield",
        appearance: "none"
    },
    submitButton: {
        width: "100%",
        padding: "16px",
        background: "#38BDF8",
        color: "#0F172A",
        border: "none",
        borderRadius: "12px",
        fontSize: "17px",
        fontWeight: 600,
        cursor: "pointer",
        marginTop: "10px"
    },
    submitButtonBig: {
        width: "100%",
        padding: "18px",
        background: "#38BDF8", //background: "#22C55E",
        color: "#0F172A",//color: "#0F172A",
        border: "none",
        borderRadius: "12px",
        fontSize: "18px",
        fontWeight: 600,
        cursor: "pointer",
        margin: "30px 0 20px 0"
    },
    addButton: {
        background: "#38BDF8",
        color: "#0F172A",
        border: "none",
        padding: "12px 32px",
        borderRadius: "12px",
        fontSize: "16px",
        fontWeight: 600,
        cursor: "pointer"
    },
    removeButton: {
        position: "absolute",
        top: "20px",
        right: "20px",
        background: "#EF4444",
        color: "white",
        border: "none",
        width: "38px",
        height: "38px",
        borderRadius: "50%",
        cursor: "pointer",
        fontSize: "18px",
        zIndex: 3
    },
    backToMenu: {
        display: "block",
        margin: "30px auto 0",
        background: "transparent",
        border: "1px solid #64748B",
        color: "#94A3B8",
        padding: "12px 28px",
        borderRadius: "12px",
        cursor: "pointer"
    }
};

export default ConstructorPage;