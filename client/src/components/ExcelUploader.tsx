import React, { useState } from 'react';
import axios from 'axios';

const ExcelUploader: React.FC = () => {
    const [dragActive, setDragActive] = useState<boolean>(false);
    const [uploading, setUploading] = useState<boolean>(false);
    const [message, setMessage] = useState<string>('');

    const handleDrag = (e: React.DragEvent<HTMLDivElement>) => {
        e.preventDefault();
        e.stopPropagation();
        setDragActive(e.type === "dragenter" || e.type === "dragover");
    };

    const handleDrop = async (e: React.DragEvent<HTMLDivElement>) => {
        e.preventDefault();
        e.stopPropagation();
        setDragActive(false);

        const file = e.dataTransfer.files?.[0];
        if (file && file.name.endsWith('.xlsx')) {
            await uploadFile(file);
        } else {
            setMessage('❌ Пожалуйста, загрузите файл .xlsx');
        }
    };

    const uploadFile = async (file: File) => {
        setUploading(true);
        setMessage('');

        const formData = new FormData();
        formData.append('file', file);

        try {
            await axios.post('http://localhost:5000/upload', formData, {
                headers: {
                    'Content-Type': 'multipart/form-data'
                },
                params: {
                    days: 30
                }
            });
            setMessage('✅ Файл успешно загружен!');
        } catch (error: any) {
            console.error('Подробная ошибка загрузки:');
            console.dir(error);

            if (error.response) {
                setMessage(`❌ Ошибка сервера: ${error.response.status}`);
            } else if (error.request) {
                setMessage('❌ Сервер не отвечает. Проверьте, запущен ли server.js');
            } else {
                setMessage('❌ Ошибка при отправке запроса');
            }
        } finally {
            setUploading(false);
        }
    };

    return (
        <div style={styles.pageWrapper}>
            <h2 style={styles.title}>
                Перетащите excel-файл с инцидентами <span style={styles.highlight}>в область ниже</span>
            </h2>

            <div
                onDragEnter={handleDrag}
                onDragLeave={handleDrag}
                onDragOver={handleDrag}
                onDrop={handleDrop}
                onClick={() => document.getElementById('fileInput')?.click()}
                style={{
                    ...styles.cloudCard,
                    ...(dragActive ? styles.cloudCardActive : {})
                }}
            >
                <div style={{ ...styles.iconWrapper, ...(dragActive ? styles.iconActive : {}) }}>
                    <svg width="120" height="120" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <path d="M11.5 15.5V8.5M11.5 8.5L8.5 11.5M11.5 8.5L14.5 11.5" stroke="#38BDF8" strokeWidth="1" strokeLinecap="round" strokeLinejoin="round" />
                        <path d="M16 16.5C18.5 16.5 20.5 14.5 20.5 12C20.5 9.5 18.5 7.5 16 7.5C15.8 7.5 15.6 7.5 15.4 7.55C14.8 5.45 12.8 4 10.5 4C7.5 4 5 6.5 5 9.5C5 9.75 5.02 10 5.06 10.25C3.3 11 2 12.85 2 15C2 17.75 4.25 20 7 20H15.5" stroke="#64748B" strokeWidth="1" strokeLinecap="round" strokeLinejoin="round" />
                    </svg>
                </div>

                <input
                    id="fileInput"
                    type="file"
                    accept=".xlsx"
                    onChange={(e) => {
                        const file = e.target.files?.[0];
                        if (file) uploadFile(file);
                    }}
                    style={{ display: 'none' }}
                />
            </div>

            <div style={styles.messageContainer}>
                {uploading && <div style={styles.loader}>Загружаем файл на сервер...</div>}
                {message && (
                    <div style={{
                        ...styles.statusMessage,
                        color: message.includes('✅') ? '#22C55E' : '#EF4444',
                        backgroundColor: message.includes('✅') ? '#14532D' : '#7F1D1D'
                    }}>
                        {message}
                    </div>
                )}
            </div>
        </div>
    );
};

const styles: { [key: string]: React.CSSProperties } = {
    pageWrapper: {
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: '87vh', //'80vh',
        backgroundColor: '#0F172A',
        fontFamily: 'sans-serif',
        color: '#F8FAFC',
        //margin: 0,
        //padding: '40px 20px',
        //boxSizing: 'border-box'
    },
    title: {
        fontSize: '32px',
        fontWeight: 300,
        color: '#F8FAFC',
        marginBottom: '40px', //'40px',
        textAlign: 'center',
    },
    highlight: {
        color: '#38BDF8',
        fontWeight: 400,
    },
    cloudCard: {
        width: '500px',
        height: '300px',
        backgroundColor: '#1E293B',
        borderRadius: '80px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        cursor: 'pointer',
        transition: 'all 0.4s ease',
        boxShadow: '0 4px 20px rgba(0,0,0,0.3)',
        border: '1px solid #334155',
    },
    cloudCardActive: {
        transform: 'scale(1.05)',
        boxShadow: '0 20px 40px rgba(56, 189, 248, 0.25)',
        borderColor: '#38BDF8',
    },
    iconWrapper: {
        transition: 'transform 0.5s ease',
    },
    iconActive: {
        transform: 'translateY(-10px)',
    },
    messageContainer: {
        height: '100px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        marginTop: '20px',
    },
    statusMessage: {
        padding: '12px 30px',
        borderRadius: '50px',
        fontSize: '16px',
        fontWeight: 500,
    },
    loader: {
        color: '#94A3B8',
        fontSize: '16px',
    }
};

export default ExcelUploader;